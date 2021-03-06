from utils import SYM2ID, ROOT_DIR, IMG_DIR, NULL, IMG_TRANSFORM
from copy import deepcopy
import random
import json
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
from torch.utils.data.dataloader import default_collate

class HINT(Dataset):
    def __init__(self, split='train', exclude_symbols=None, max_len=None, n_sample_zero_res=None, numSamples=None, randomSeed=None):
        super(HINT, self).__init__()
        
        assert split in ['train', 'val', 'test']
        self.split = split
        self.dataset = json.load(open(ROOT_DIR + 'expr_%s.json'%split))
        if numSamples:
            if randomSeed:
                random.seed(randomSeed)
                random.shuffle(self.dataset)
            self.dataset = self.dataset[:numSamples]
        
        if exclude_symbols is not None:
            exclude_symbols = set(exclude_symbols)
            self.dataset = [x for x in self.dataset if len(set(x['expr']) & exclude_symbols) == 0]

        if n_sample_zero_res is not None:
            samples_non_zero = [x for x in self.dataset if len(x['expr']) == 1 or (x['res'] != 0 and '0' not in x['expr'])]
            samples_zero = [x for x in self.dataset if len(x['expr']) > 1 and (x['res'] == 0 or '0' in x['expr'])]
            samples_zero = random.sample(samples_zero, int(len(samples_zero) * n_sample_zero_res))
            self.dataset = samples_non_zero + samples_zero
        
        if max_len is not None:
            self.dataset = [x for x in self.dataset if len(x['expr']) <= max_len]
            
        for x in self.dataset:
            x['len'] = len(x['expr'])
        
        self.img_transform = IMG_TRANSFORM
        self.valid_ids = list(range(len(self.dataset)))

        # dataset statistics, used to filter samples
        len2ids = {}
        for i, x in enumerate(self.dataset):
            l = len(x['img_paths'])
            if l not in len2ids:
                len2ids[l] = []
            len2ids[l].append(i)
        self.len2ids = len2ids

        sym2ids = {}
        for i, x in enumerate(self.dataset):
            for s in list(set(x['expr'])):
                if s not in sym2ids:
                    sym2ids[s] = []
                sym2ids[s].append(i)
        self.sym2ids = sym2ids

        res2ids = {}
        for i, x in enumerate(self.dataset):
            l = x['res']
            if l not in res2ids:
                res2ids[l] = []
            res2ids[l].append(i)
        self.res2ids = res2ids

        digit2ids = {}
        for i, x in enumerate(self.dataset):
            if len(x['expr']) == 1:
                s = x['expr'][0]
                if s not in digit2ids:
                    digit2ids[s] = []
                digit2ids[s].append(i)
        self.digit2ids = digit2ids


    def __getitem__(self, index):
        index = self.valid_ids[index]
        sample = deepcopy(self.dataset[index])
        img_seq = []
        for img_path in sample['img_paths']:
            img = Image.open(IMG_DIR+img_path).convert('L')
            #print(img.size, img.mode)
            img = self.img_transform(img)
            img_seq.append(img)
        # del sample['img_paths']
        sample['expr'] = ''.join(sample['expr'])
        
        label_seq = [SYM2ID[sym] for sym in sample['expr']]
        sample['img_seq'] = img_seq
        sample['label_seq'] = label_seq
        return sample
            
    
    def __len__(self):
        return len(self.valid_ids)

    def filter_by_len(self, min_len=None, max_len=None):
        if min_len is None: min_len = -1
        if max_len is None: max_len = 1e7
        self.valid_ids = [i for i, x in enumerate(self.dataset) if x['len'] <= max_len and x['len'] >= min_len]

def HINT_collate(batch):
    max_len = np.max([x['len'] for x in batch])
    zero_img = torch.zeros_like(batch[0]['img_seq'][0])
    img_paths_list = []
    head_list = []
    for sample in batch:
        sample['img_seq'] += [zero_img] * (max_len - sample['len'])
        sample['img_seq'] = torch.stack(sample['img_seq'])
        
        sample['label_seq'] += [SYM2ID[NULL]] * (max_len - sample['len'])
        sample['label_seq'] = torch.tensor(sample['label_seq'])

        # sample['head'] += [-2] * (max_len - sample['len'])
        # sample['head'] = torch.tensor(sample['head'])
        img_paths_list.append(sample['img_paths'])
        del sample['img_paths']

        head_list.append(sample['head'])
        del sample['head']
        
    batch = default_collate(batch)
    batch['img_paths'] = img_paths_list
    batch['head'] = head_list
    return batch

if __name__ == '__main__':
    val_set = HINT('val')
    val_loader = DataLoader(val_set, batch_size=32,
                         shuffle=True, num_workers=4, collate_fn=HINT_collate)

    print(next(iter(val_loader)))