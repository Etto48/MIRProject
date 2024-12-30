import os
import requests
import torch
from torch import nn
from tqdm.auto import tqdm
import transformers

from mir import DATA_DIR
from mir.neural_relevance.dataset import MSMarcoDataset

class NeuralRelevance(nn.Module):
    def __init__(self):
        super().__init__()
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu")
        
        model_name = "bert-large-uncased"
        self.tokenizer = transformers.BertTokenizer.from_pretrained(model_name)
        self.model = transformers.BertModel.from_pretrained(model_name).to(self.device)
        for param in self.model.parameters():
            param.requires_grad = False
        
        bert_embedding_size = self.model.config.hidden_size
        self.similairty_head = nn.Sequential(
            nn.Linear(bert_embedding_size, 1, device=self.device),
            nn.Sigmoid()
        ).to(self.device)
        

    def forward(self, x: dict) -> torch.Tensor:
        x = self.model(**x).last_hidden_state
        features = x[:, 0, :]
        x = self.similairty_head(features)
        return x.squeeze()

    def preprocess(self, queries: list[str], documents: list[str]) -> dict:
        tokens = self.tokenizer(queries, documents, return_tensors="pt", padding=True).to(self.device)
        return tokens

    def forward_queries_and_documents(self, queries: list[str], documents: list[str]) -> torch.Tensor:
        x = self.preprocess(queries, documents)
        return self.forward(x)

    def loss(
        self,
        similarity: torch.Tensor,
        relevance: torch.Tensor,
    ):
        ce_similarity_loss = torch.nn.functional.binary_cross_entropy(similarity, relevance / 5)
        mse_similarity_loss = torch.nn.functional.mse_loss(similarity, relevance / 5)
        return ce_similarity_loss, mse_similarity_loss, ce_similarity_loss

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
        optimizer = torch.optim.AdamW(self.parameters(), lr=1e-4, weight_decay=1)
        best_loss = float("inf")
        best_model = None
        patience = 3
        threshold = 0.001
        epochs_without_improvement = 0

        history = {
            "train_ce": [], "valid_ce": [],
            "train_mse": [], "valid_mse": [],
        }

        for epoch in range(epochs):
            self.train()
            avg_ce = 0
            avg_mse = 0
            batches = tqdm(train_loader, desc=f"Epoch {epoch + 1}/{epochs} (train)", total=len(train_loader))
            for i, (queries, docs, relevances) in enumerate(batches):
                relevances = relevances.to(self.device)
                optimizer.zero_grad()
                similarity = self.forward_queries_and_documents(queries, docs)
                ce, mse, loss = self.loss(similarity, relevances)
                avg_ce += ce.item()
                avg_mse += mse.item()
                batches.set_postfix(
                    ce=avg_ce / (i + 1), 
                    mse=avg_mse / (i + 1))
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.parameters(), 1)
                optimizer.step()
            avg_ce /= (i + 1)
            avg_mse /= (i + 1)
            history["train_ce"].append(avg_ce)
            history["train_mse"].append(avg_mse)
            self.eval()
            with torch.no_grad():
                avg_ce = 0
                avg_mse = 0
                avg_loss = 0
                batches = tqdm(valid_loader, desc=f"Epoch {epoch + 1}/{epochs} (valid)", total=len(valid_loader))
                for i, (queries, docs, relevances) in enumerate(batches):
                    relevances = relevances.to(self.device)
                    similarity = self.forward_queries_and_documents(queries, docs)
                    ce, mse, loss = self.loss(similarity, relevances)
                    avg_ce += ce.item()
                    avg_mse += mse.item()
                    avg_loss += loss.item()
                    batches.set_postfix(
                        ce=avg_ce / (i + 1),
                        mse=avg_mse / (i + 1))
                avg_ce /= (i + 1)
                avg_mse /= (i + 1)
                history["valid_ce"].append(avg_ce)
                history["valid_mse"].append(avg_mse)
                if avg_loss < best_loss - threshold:
                    best_loss = avg_loss
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
    
    @staticmethod
    def from_pretrained():
        if not os.path.exists(f"{DATA_DIR}/neural_relevance.pt"):
            url = "https://huggingface.co/Etto48/MIRProject/resolve/main/neural_relevance.pt"
            weights_request = requests.get(url)
            weights_request.raise_for_status()
            with tqdm(total=int(weights_request.headers["Content-Length"]), unit="B", unit_scale=True, desc="Downloading weights") as pbar:
                with open(f"{DATA_DIR}/neural_relevance.pt", "wb") as f:
                    for chunk in weights_request.iter_content(chunk_size=1024):
                        f.write(chunk)
                        pbar.update(len(chunk))
        model = NeuralRelevance.load(f"{DATA_DIR}/neural_relevance.pt")
        return model


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    train = MSMarcoDataset.load("train")
    valid = MSMarcoDataset.load("valid")
    model = NeuralRelevance()
    try:
        history = model.fit(train, valid)
        model.save(f"{DATA_DIR}/neural_relevance.pt")
        plt.subplot(1, 2, 1)
        plt.plot(history["train_ce"], label="train")
        plt.plot(history["valid_ce"], label="valid")
        plt.title("Cross Entropy Loss")
        plt.legend()
        plt.subplot(1, 2, 2)
        plt.plot(history["train_mse"], label="train")
        plt.plot(history["valid_mse"], label="valid")
        plt.title("Mean Squared Error Loss")
        plt.legend()
        plt.show()
    except KeyboardInterrupt:
        pass
