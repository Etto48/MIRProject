import numpy as np
import torch
from torch import nn

class PositionalEncoding(nn.Module):
    def __init__(self):
        super().__init__()
        self.pe = None

    def set_pe(self, t, d, device):
        position = torch.arange(t, device=device).view(1, -1, 1)
        div_term = torch.exp(torch.arange(0, d, 2, device=device) * -np.log(10000.0) / d).view(1, 1, -1)
        self.pe = torch.zeros(1, t, d, device=device)
        self.pe[:, :, 0::2] = torch.sin(position * div_term)
        self.pe[:, :, 1::2] = torch.cos(position * div_term)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        _, t, d = x.size()
        if self.pe is None or t > self.pe.size(1) or d != self.pe.size(2) or self.pe.device != x.device:
            self.set_pe(t, d, x.device)

        x = x + self.pe[:, :t, :]
        return x