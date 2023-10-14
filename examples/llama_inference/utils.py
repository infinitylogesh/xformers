from torch.utils.data import IterableDataset,Dataset
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset
import torch
import json,gzip
from typing import Dict,Iterable
import os
from datasets import load_dataset

class ConstantLengthDataset(IterableDataset):
    """
    Iterable dataset that returns constant length chunks of tokens from stream of text files.
        Args:
            tokenizer (Tokenizer): The processor used for proccessing the data.
            dataset (dataset.Dataset): Dataset with text files.
            infinite (bool): If True the iterator is reset after dataset reaches end else stops.
            seq_length (int): Length of token sequences to return.
            num_of_sequences (int): Number of token sequences to keep in buffer.
            chars_per_token (int): Number of characters per token used to estimate number of tokens in text buffer.
    """

    def __init__(
        self,
        tokenizer,
        dataset,
        infinite=False,
        seq_length=1024,
        num_of_sequences=1024,
        chars_per_token=3.6,
    ):
        self.tokenizer = tokenizer
        self.concat_token_id = tokenizer.eos_token_id if tokenizer.eos_token_id is not None else args.eos_token_id
        self.dataset = dataset.shuffle(seed=42)["train"]
        self.seq_length = seq_length
        self.infinite = infinite
        self.current_size = 0
        self.max_buffer_size = seq_length * chars_per_token * num_of_sequences
    
    def fetch_content(self,item):
        return item["content"]

    def __iter__(self):
        iterator = iter(self.dataset)
        more_examples = True
        while more_examples:
            buffer, buffer_len = [], 0
            while True:
                if buffer_len >= self.max_buffer_size:
                    break
                try:
                    buffer.append(self.fetch_content(next(iterator)))
                    buffer_len += len(buffer[-1])
                except StopIteration:
                    if self.infinite:
                        iterator = iter(self.dataset)
                    else:
                        more_examples = False
                        break
            tokenized_inputs = self.tokenizer(buffer, truncation=False)["input_ids"]
            all_token_ids = []
            for tokenized_input in tokenized_inputs:
                all_token_ids.extend(tokenized_input + [self.concat_token_id])
            for i in range(0, len(all_token_ids), self.seq_length):
                input_ids = all_token_ids[i : i + self.seq_length]
                if len(input_ids) == self.seq_length:
                    self.current_size += 1
                    yield {
                        "input_ids": torch.LongTensor(input_ids),
                        "text": self.tokenizer.batch_decode([input_ids], skip_special_tokens=True),
                    }


def _fetch_constantlength_inputs(
    batch_size,
    tokenizer,
    per_seq_input_token_length,
    dataset_name="bigcode/the-stack-smol",
    subset="data/python",
):
    total_batch_tokens = 0
    ds = load_dataset(dataset_name, data_dir=subset)
    cds = ConstantLengthDataset(
        tokenizer=tokenizer,
        dataset=ds,
        seq_length=per_seq_input_token_length,
        num_of_sequences=1,
    )
    input_sentences = []
    iter_cds = iter(cds)
    for _ in range(batch_size):
        _item = next(iter_cds)
        input_sentences.append(_item["text"][0])
        total_batch_tokens+=_item['input_ids'].shape[-1]
    print(len(input_sentences), batch_size, input_sentences[0])
    print(f"Per batch input token length: {total_batch_tokens}")
    return input_sentences