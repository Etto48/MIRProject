import torch
from torch import nn
import tiktoken
from tqdm.auto import tqdm

from mir.neural_relevance.dataset import MSMarcoDataset
from mir.neural_relevance.pos_enc import PositionalEncoding

class NeuralRelevance(nn.Module):
    def __init__(self):
        super().__init__()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.embedding_dim = 512
        self.nhead = 8
        self.num_layers = 6
        self.dim_feedforward = self.embedding_dim * 4
        self.dropout = 0.1

        self.tokenizer = tiktoken.get_encoding("gpt2")
        self.embedding = nn.Embedding(
            num_embeddings=self.tokenizer.max_token_value + 1,
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
            norm=nn.LayerNorm(self.embedding_dim),
            enable_nested_tensor=True
        )
        self.cls_token = nn.Parameter(torch.randn(1, 1, self.embedding_dim, device=self.device))
    
    def forward(self, x: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        x = self.embedding(x)
        x = torch.cat([self.cls_token.expand(x.size(0), -1, -1), x], dim=1)
        x = self.positional_encoding(x)
        x = self.encoder(x, src_key_padding_mask=self.padding_mask_from_lengths(lengths))
        return x[:, 0, :]
    
    def preprocess(self, text: list[str]):
        tokens = [self.tokenizer.encode(t) for t in text]
        lengths = [len(t) for t in tokens]
        max_len = max(lengths)
        tokens = torch.tensor([t + [self.tokenizer.max_token_value] * (max_len - len(t)) for t in tokens], device=self.device)
        lengths = torch.tensor(lengths, device=self.device, dtype=torch.long)
        
        return tokens, lengths

    def padding_mask_from_lengths(self, lengths: torch.Tensor) -> torch.Tensor:
        max_len = lengths.max()
        mask = torch.arange(max_len + 1, device=self.device).expand(len(lengths), max_len + 1) > lengths.unsqueeze(1)
        return mask

    def forward_queries_and_documents(self, queries: list[str], documents: list[str]) -> torch.Tensor:
        query_tokens, query_lengths = self.preprocess(queries)
        query_features = self.forward(query_tokens, query_lengths)

        doc_tokens, doc_lengths = self.preprocess(documents)
        doc_features = self.forward(doc_tokens, doc_lengths)

        return self.similarity(query_features, doc_features)

    def similarity(self, query_features: torch.Tensor, document_features: torch.Tensor) -> torch.Tensor:
        return (torch.nn.functional.cosine_similarity(query_features, document_features, dim=-1) + 1) / 2
    
    def loss(self, similarity: torch.Tensor, relevance: torch.Tensor) -> torch.Tensor:
        return torch.nn.functional.mse_loss(similarity, relevance / 5)

    def fit(self, train: MSMarcoDataset, valid: MSMarcoDataset, epochs: int = 100):
        bs = 32
        train_loader = torch.utils.data.DataLoader(train, batch_size=bs, shuffle=True, collate_fn=MSMarcoDataset.collate_fn)
        valid_loader = torch.utils.data.DataLoader(valid, batch_size=bs, shuffle=False, collate_fn=MSMarcoDataset.collate_fn)
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-4)
        for epoch in range(epochs):
            self.train()
            avg_loss = 0
            batches = tqdm(train_loader, desc=f"Epoch {epoch + 1}/{epochs} (train)", total=len(train_loader))
            for i, (queries, docs, relevances) in enumerate(batches):
                relevances = relevances.to(self.device)
                optimizer.zero_grad()
                similarity = self.forward_queries_and_documents(queries, docs)
                loss = self.loss(similarity, relevances)
                avg_loss += loss.item()
                batches.set_postfix(loss=avg_loss / (i + 1))
                loss.backward()
                optimizer.step()
            self.eval()
            with torch.no_grad():
                avg_loss = 0
                batches = tqdm(valid_loader, desc=f"Epoch {epoch + 1}/{epochs} (valid)", total=len(valid_loader))
                for i, (queries, docs, relevances) in enumerate(batches):
                    relevances = relevances.to(self.device)
                    similarity = self.forward_queries_and_documents(queries, docs)
                    loss = self.loss(similarity, relevances)
                    avg_loss += loss.item()
                    batches.set_postfix(loss=avg_loss / (i + 1))

if __name__ == "__main__":
    train = MSMarcoDataset.load("train")
    valid = MSMarcoDataset.load("valid")
    model = NeuralRelevance()
    model.fit(train, valid)