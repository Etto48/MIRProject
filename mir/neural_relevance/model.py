import torch
from torch import nn
import tiktoken
from tqdm.auto import tqdm

from mir import DATA_DIR
from mir.neural_relevance.dataset import MSMarcoDataset
from mir.neural_relevance.pos_enc import PositionalEncoding


class NeuralRelevance(nn.Module):
    def __init__(self):
        super().__init__()
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu")
        self.embedding_dim = 16
        self.nhead = 4
        self.num_layers = 4
        self.dim_feedforward = self.embedding_dim
        self.dropout = 0.6

        self.tokenizer = tiktoken.get_encoding("gpt2")
        self.embedding = nn.Embedding(
            num_embeddings=self.tokenizer.max_token_value + 2,
            embedding_dim=self.embedding_dim,
            device=self.device
        )
        self.positional_encoding = PositionalEncoding()

        self.encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=self.embedding_dim,
                nhead=self.nhead,
                dim_feedforward=self.dim_feedforward,
                dropout=self.dropout,
                batch_first=True,
                device=self.device
            ),
            num_layers=self.num_layers,
            norm=nn.LayerNorm(self.embedding_dim, device=self.device),
            enable_nested_tensor=False
        )
        self.cls_token = nn.Parameter(torch.randn(
            1, 1, self.embedding_dim, device=self.device))
        self.mask_token_id = self.tokenizer.max_token_value + 1
        self.cls_projection = nn.Sequential(
            nn.Dropout(self.dropout),
            nn.Linear(self.embedding_dim, self.embedding_dim, device=self.device),
        )
        self.deembedding = nn.Sequential(
            nn.Dropout(self.dropout),
            nn.Linear(self.embedding_dim,
                      self.tokenizer.max_token_value + 1, device=self.device),
        )

    def forward(self, x: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        x = self.embedding(x)
        x = torch.cat([self.cls_token.expand(x.size(0), -1, -1), x], dim=1)
        x = self.positional_encoding(x)
        x = self.encoder(
            x, src_key_padding_mask=self.padding_mask_from_lengths(lengths))
        cls_token = x[:, 0, :]
        output_sequence = x[:, 1:, :]
        cls_token = self.cls_projection(cls_token)
        output_sequence = self.deembedding(output_sequence)
        return cls_token, output_sequence

    def preprocess(self, text: list[str]):
        tokens = [self.tokenizer.encode(t) for t in text]
        lengths = [len(t) for t in tokens]
        max_len = max(lengths)
        tokens = torch.tensor([t + [self.tokenizer.max_token_value]
                              * (max_len - len(t)) for t in tokens], device=self.device)
        lengths = torch.tensor(lengths, device=self.device, dtype=torch.long)

        return tokens, lengths

    def padding_mask_from_lengths(self, lengths: torch.Tensor) -> torch.Tensor:
        max_len = lengths.max()
        mask = torch.arange(max_len + 1, device=self.device).expand(
            len(lengths), max_len + 1) > lengths.unsqueeze(1)
        return mask

    def forward_queries_and_documents(self, queries: list[str], documents: list[str]) -> tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor]]:
        query_tokens_og, query_lengths = self.preprocess(queries)
        if self.training:
            query_tokens, query_mask = self.random_mask_tokens(query_tokens_og, query_lengths)
        else:
            query_tokens = query_tokens_og
            query_mask = torch.zeros_like(query_tokens, dtype=torch.bool)
        query_features, query_reconstruction = self.forward(
            query_tokens, query_lengths)

        doc_tokens_og, doc_lengths = self.preprocess(documents)
        if self.training:
            doc_tokens, doc_mask = self.random_mask_tokens(doc_tokens_og, doc_lengths)
        else:
            doc_tokens = doc_tokens_og
            doc_mask = torch.zeros_like(doc_tokens, dtype=torch.bool)
        doc_features, doc_reconstruction = self.forward(
            doc_tokens, doc_lengths)

        return self.similarity(query_features, doc_features), (query_tokens_og, doc_tokens_og, query_reconstruction, doc_reconstruction, query_mask, doc_mask)

    def random_mask_tokens(self, tokens: torch.Tensor, lengths: torch.Tensor, mask_prob: float = 0.15) -> tuple[torch.Tensor, torch.Tensor]:
        padding_mask = self.padding_mask_from_lengths(lengths)[:, 1:]
        mask = torch.rand(tokens.size(), device=self.device) < mask_prob
        keep_mask = torch.rand(tokens.size(), device=self.device) < 0.1
        random_mask = torch.rand(tokens.size(), device=self.device) < 0.1
        replacement_tokens = torch.randint(
            0, self.tokenizer.max_token_value, tokens.size(), device=self.device)
        mask = mask & ~padding_mask
        masked_tokens = tokens.clone()
        masked_tokens[mask & ~keep_mask] = self.mask_token_id
        masked_tokens[mask & ~keep_mask & random_mask] = replacement_tokens[mask & ~keep_mask & random_mask]
        return masked_tokens, mask

    def similarity(self, query_features: torch.Tensor, document_features: torch.Tensor) -> torch.Tensor:
        return (torch.nn.functional.cosine_similarity(query_features, document_features, dim=-1) + 1) / 2

    def loss(
        self,
        similarity: torch.Tensor,
        relevance: torch.Tensor,
        query: torch.Tensor,
        doc: torch.Tensor,
        query_reconstruction: torch.Tensor,
        doc_reconstruction: torch.Tensor,
        query_mask: torch.Tensor,
        doc_mask: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        similarity_loss = torch.nn.functional.binary_cross_entropy(similarity, relevance / 5)
        mse_similarity_loss = torch.nn.functional.mse_loss(similarity, relevance / 5)
        query_prob_mask = query_mask.unsqueeze(-1).expand_as(query_reconstruction)
        query_recon_loss = torch.nn.functional.cross_entropy(
            query_reconstruction[query_prob_mask].view(-1, query_reconstruction.size(-1)),
            query[query_mask]
        )
        doc_prob_mask = doc_mask.unsqueeze(-1).expand_as(doc_reconstruction)
        doc_recon_loss = torch.nn.functional.cross_entropy(
            doc_reconstruction[doc_prob_mask].view(-1, doc_reconstruction.size(-1)),
            doc[doc_mask]
        )
        l1_regularization = 0
        numel = 0
        for p in self.parameters():
            numel += p.numel()
            l1_regularization += p.abs().sum()
        l1_regularization /= numel
        return similarity_loss, mse_similarity_loss, query_recon_loss, doc_recon_loss, l1_regularization


    def fit(self, train: MSMarcoDataset, valid: MSMarcoDataset, epochs: int = 100):
        bs = 16
        train_loader = torch.utils.data.DataLoader(
            train,
            batch_size=bs,
            collate_fn=MSMarcoDataset.collate_fn,
            sampler=torch.utils.data.RandomSampler(
                train, replacement=True, num_samples=bs * 100)
        )
        valid_loader = torch.utils.data.DataLoader(
            valid,
            batch_size=bs,
            collate_fn=MSMarcoDataset.collate_fn,
            sampler=torch.utils.data.RandomSampler(
                valid, replacement=True, num_samples=bs * 50)
        )
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-4)
        best_loss = float("inf")
        best_model = None
        patience = 3
        threshold = 0.001
        epochs_without_improvement = 0

        history = {"train_similarity_loss": [], "valid_similarity_loss": []}

        for epoch in range(epochs):
            self.train()
            avg_similarity_loss = 0
            avg_mse = 0
            avg_query_recon_loss = 0
            avg_doc_recon_loss = 0
            batches = tqdm(train_loader, desc=f"Epoch {epoch + 1}/{epochs} (train)", total=len(train_loader))
            for i, (queries, docs, relevances) in enumerate(batches):
                relevances = relevances.to(self.device)
                optimizer.zero_grad()
                similarity, (query_tokens_og, doc_tokens_og, query_reconstruction, doc_reconstruction, query_mask, doc_mask) = \
                    self.forward_queries_and_documents(queries, docs)
                similarity_loss, mse, query_recon_loss, doc_recon_loss, l1_regularization = \
                    self.loss(similarity, relevances, query_tokens_og, doc_tokens_og, query_reconstruction, doc_reconstruction, query_mask, doc_mask)
                avg_similarity_loss += similarity_loss.item()
                avg_mse += mse.item()
                avg_query_recon_loss += query_recon_loss.item()
                avg_doc_recon_loss += doc_recon_loss.item()
                loss = similarity_loss + 2 * l1_regularization #+ query_recon_loss + doc_recon_loss
                batches.set_postfix(
                    sim=avg_similarity_loss / (i + 1), 
                    mse=avg_mse / (i + 1),
                    q=avg_query_recon_loss / (i + 1), 
                    d=avg_doc_recon_loss / (i + 1),
                    l1=l1_regularization.item())
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.parameters(), 1)
                optimizer.step()
            avg_similarity_loss /= (i + 1)
            history["train_similarity_loss"].append(avg_similarity_loss)
            self.eval()
            with torch.no_grad():
                avg_similarity_loss = 0
                avg_mse = 0
                avg_query_recon_loss = 0
                avg_doc_recon_loss = 0
                batches = tqdm(valid_loader, desc=f"Epoch {epoch + 1}/{epochs} (valid)", total=len(valid_loader))
                for i, (queries, docs, relevances) in enumerate(batches):
                    relevances = relevances.to(self.device)
                    similarity, (query_tokens_og, doc_tokens_og, query_reconstruction, doc_reconstruction, query_mask, doc_mask) = \
                        self.forward_queries_and_documents(queries, docs)
                    similarity_loss, mse, query_recon_loss, doc_recon_loss, l1_regularization = \
                        self.loss(similarity, relevances, query_tokens_og, doc_tokens_og, query_reconstruction, doc_reconstruction, query_mask, doc_mask)
                    avg_similarity_loss += similarity_loss.item()
                    avg_mse += mse.item()
                    avg_query_recon_loss += query_recon_loss.item()
                    avg_doc_recon_loss += doc_recon_loss.item()
                    batches.set_postfix(
                        sim=avg_similarity_loss / (i + 1), 
                        mse=avg_mse / (i + 1),
                        q=avg_query_recon_loss / (i + 1), 
                        d=avg_doc_recon_loss / (i + 1),
                        l1=l1_regularization.item())
                avg_similarity_loss /= (i + 1)
                history["valid_similarity_loss"].append(avg_similarity_loss)
                if avg_similarity_loss < best_loss - threshold:
                    best_loss = avg_similarity_loss
                    best_model = self.state_dict()
                    epochs_without_improvement = 0
                else:
                    epochs_without_improvement += 1
                    if epochs_without_improvement >= patience:
                        break
        self.load_state_dict(best_model)
        return history
    
    def save(self, path: str):
        torch.save(self.state_dict(), path)
    
    @staticmethod
    def load(path: str):
        model = NeuralRelevance()
        model.load_state_dict(torch.load(path, map_location=model.device, weights_only=True))
        return model

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    train = MSMarcoDataset.load("train")
    valid = MSMarcoDataset.load("valid")
    model = NeuralRelevance()
    try:
        history = model.fit(train, valid)
        model.save(f"{DATA_DIR}/neural_relevance.pth")
        plt.plot(history["train_similarity_loss"], label="Train Similarity Loss")
        plt.plot(history["valid_similarity_loss"], label="Valid Similarity Loss")
        plt.legend()
        plt.show()
    except KeyboardInterrupt:
        pass
