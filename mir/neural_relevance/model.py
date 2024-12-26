import torch
from torch import nn
import tiktoken
from tqdm.auto import tqdm
import transformers

from mir import DATA_DIR
from mir.neural_relevance.dataset import MSMarcoDataset

class NeuralRelevance(nn.Module):
    def __init__(self):
        super().__init__()
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu")
        
        self.tokenizer = transformers.BertTokenizer.from_pretrained("bert-base-uncased")
        self.model = transformers.BertModel.from_pretrained("bert-base-uncased").to(self.device)
        for param in self.model.parameters():
            param.requires_grad = False
        
        bert_embedding_size = self.model.config.hidden_size
        self.similairty_head = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(bert_embedding_size, 1, device=self.device),
            #nn.Sigmoid()
        )

    def forward(self, x: dict) -> torch.Tensor:
        x = self.model(**x).last_hidden_state
        features = x[:, 0, :]
        x = self.similairty_head(features)
        return x.squeeze()

    def preprocess(self, text: list[str]):
        tokens = self.tokenizer(text, return_tensors="pt", padding=True).to(self.device)
        return tokens

    def forward_queries_and_documents(self, queries: list[str], documents: list[str]) -> torch.Tensor:
        qd = []
        for q, d in zip(queries, documents):
            qd.append(q + "[SEP]" + d)
        x = self.preprocess(qd)
        return self.forward(x)

    def loss(
        self,
        similarity: torch.Tensor,
        relevance: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        similarity_loss = torch.nn.functional.binary_cross_entropy_with_logits(similarity, relevance)
        mse_similarity_loss = torch.nn.functional.mse_loss(similarity, relevance / 5)
        return similarity_loss, mse_similarity_loss

    def fit(self, train: MSMarcoDataset, valid: MSMarcoDataset, epochs: int = 100):
        bs = 256
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
        optimizer = torch.optim.AdamW(self.parameters(), lr=5e-5, weight_decay=0.1)
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
            batches = tqdm(train_loader, desc=f"Epoch {epoch + 1}/{epochs} (train)", total=len(train_loader))
            for i, (queries, docs, relevances) in enumerate(batches):
                relevances = relevances.to(self.device)
                optimizer.zero_grad()
                similarity = self.forward_queries_and_documents(queries, docs)
                similarity_loss, mse = self.loss(similarity, relevances)
                avg_similarity_loss += similarity_loss.item()
                avg_mse += mse.item()
                loss = mse
                batches.set_postfix(
                    sim=avg_similarity_loss / (i + 1), 
                    mse=avg_mse / (i + 1))
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.parameters(), 1)
                optimizer.step()
            avg_similarity_loss /= (i + 1)
            history["train_similarity_loss"].append(avg_mse)
            self.eval()
            with torch.no_grad():
                avg_similarity_loss = 0
                avg_mse = 0
                batches = tqdm(valid_loader, desc=f"Epoch {epoch + 1}/{epochs} (valid)", total=len(valid_loader))
                for i, (queries, docs, relevances) in enumerate(batches):
                    relevances = relevances.to(self.device)
                    similarity = self.forward_queries_and_documents(queries, docs)
                    similarity_loss, mse = self.loss(similarity, relevances)
                    avg_similarity_loss += similarity_loss.item()
                    avg_mse += mse.item()
                    batches.set_postfix(
                        sim=avg_similarity_loss / (i + 1), 
                        mse=avg_mse / (i + 1))
                avg_similarity_loss /= (i + 1)
                history["valid_similarity_loss"].append(avg_mse)
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
