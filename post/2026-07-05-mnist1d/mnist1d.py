"""MNIST-1D: a procedurally generated 1D analogue of MNIST.

Faithful reimplementation of Greydanus & Steinbach's construction
(https://arxiv.org/abs/2011.14439, https://github.com/greydanus/mnist1d).

Each of 10 class templates (12-point hand-drawn digit shapes) is turned into
many examples by a randomized pipeline: padding, resampling, scaling,
translation, correlated background noise, iid noise, and a linear shear. The
result is a length-40 sequence per example.
"""

import pickle

import numpy as np
from scipy.interpolate import interp1d
from scipy.ndimage import gaussian_filter


def get_dataset_args():
    return {
        "num_samples": 5000,
        "train_split": 0.8,
        "template_len": 12,
        "padding": [36, 60],
        "scale_coeff": 0.4,
        "max_translation": 48,
        "corr_noise_scale": 0.25,
        "iid_noise_scale": 2e-2,
        "shear_scale": 0.75,
        "shuffle_seq": False,
        "final_seq_length": 40,
        "seed": 42,
    }


def get_templates():
    """The 10 base digit shapes, each a 12-point 1D signal."""
    d0 = np.asarray([5, 6, 6.5, 6.75, 7, 7, 7, 7, 6.75, 6.5, 6, 5])
    d1 = np.asarray([5, 3, 3, 3.4, 3.8, 4.2, 4.6, 5, 5.4, 5.8, 5, 5])
    d2 = np.asarray([5, 6, 6.5, 6.5, 6, 5.25, 4.75, 4, 3.5, 3.5, 4, 5])
    d3 = np.asarray([5, 6, 6.5, 6.5, 6, 5, 5, 6, 6.5, 6.5, 6, 5])
    d4 = np.asarray([5, 4.4, 3.8, 3.2, 2.6, 2.6, 5, 5, 5, 5, 5, 5])
    d5 = np.asarray([5, 3, 3, 3, 3, 5, 6, 6.5, 6.5, 6, 4.5, 5])
    d6 = np.asarray([5, 4, 3.5, 3.25, 3, 3, 3, 3, 3.25, 3.5, 4, 5])
    d7 = np.asarray([5, 7, 7, 6.6, 6.2, 5.8, 5.4, 5, 4.6, 4.2, 5, 5])
    d8 = np.asarray([5, 4, 3.5, 3.5, 4, 5, 5, 4, 3.5, 3.5, 4, 5])
    d9 = np.asarray([5, 4, 3.5, 3.5, 4, 5, 5, 5, 5, 4.7, 4.3, 5])

    x = np.stack([d0, d1, d2, d3, d4, d5, d6, d7, d8, d9])
    x -= x.mean(1, keepdims=True)
    x /= x.std(1, keepdims=True)
    x -= x[:, :1]
    return {
        "x": x / 6.0,
        "t": np.linspace(-5, 5, len(d0)) / 6.0,
        "y": np.arange(10),
    }


def pad(x, padding):
    low, high = padding
    p = low + int(np.random.rand() * (high - low + 1))
    return np.concatenate([x, np.zeros(p)])


def shear(x, scale):
    coeff = scale * (np.random.rand() - 0.5)
    return x - coeff * np.linspace(-0.5, 0.5, len(x))


def translate(x, max_translation):
    k = np.random.choice(max_translation)
    return np.concatenate([x[-k:], x[:-k]])


def corr_noise_like(x, scale):
    return gaussian_filter(scale * np.random.randn(*x.shape), 2)


def iid_noise_like(x, scale):
    return scale * np.random.randn(*x.shape)


def interpolate(x, n):
    new_scale = np.linspace(0, 1, n)
    return interp1d(np.linspace(0, 1, len(x)), x, kind="linear")(new_scale)


def transform(x, t, args, eps=1e-8):
    new_x = pad(x + eps, args["padding"])
    new_x = interpolate(new_x, args["template_len"] + args["padding"][-1])
    new_t = interpolate(t, args["template_len"] + args["padding"][-1])
    new_x *= 1 + args["scale_coeff"] * (np.random.rand() - 0.5)
    new_x = translate(new_x, args["max_translation"])

    # noise fills only the zero-padded background, signal stays clean
    mask = new_x != 0
    new_x = mask * new_x + (1 - mask) * corr_noise_like(new_x, args["corr_noise_scale"])
    new_x = new_x + iid_noise_like(new_x, args["iid_noise_scale"])

    new_x = shear(new_x, args["shear_scale"])
    new_x = interpolate(new_x, args["final_seq_length"])
    new_t = interpolate(new_t, args["final_seq_length"])
    return new_x, new_t


def make_dataset(args=None):
    args = get_dataset_args() if args is None else args
    templates = get_templates()
    np.random.seed(args["seed"])

    xs, ys = [], []
    samples_per_class = args["num_samples"] // len(templates["y"])
    for label_ix in range(len(templates["y"])):
        for _ in range(samples_per_class):
            x, new_t = transform(templates["x"][label_ix], templates["t"], args)
            xs.append(x)
            ys.append(templates["y"][label_ix])

    shuffle = np.random.permutation(len(ys))
    xs = np.stack(xs)[shuffle]
    ys = np.stack(ys)[shuffle]

    if args["shuffle_seq"]:
        xs = xs[..., np.random.permutation(args["final_seq_length"])]

    new_t = new_t / xs.std()
    xs = (xs - xs.mean()) / xs.std()

    split = int(len(ys) * args["train_split"])
    return {
        "x": xs[:split], "y": ys[:split],
        "x_test": xs[split:], "y_test": ys[split:],
        "t": new_t, "templates": templates,
    }


def get_dataset(path="mnist1d_data.pkl", regenerate=False, args=None):
    """Load the dataset from `path`, generating and caching it on first use."""
    import os

    if regenerate or not os.path.exists(path):
        data = make_dataset(args)
        with open(path, "wb") as f:
            pickle.dump(data, f, protocol=3)
        return data
    with open(path, "rb") as f:
        return pickle.load(f)


if __name__ == "__main__":
    data = get_dataset(regenerate=True)
    print("Generated MNIST-1D dataset:")
    print(f"  x      {data['x'].shape}  (train signals)")
    print(f"  y      {data['y'].shape}  (train labels)")
    print(f"  x_test {data['x_test'].shape}")
    print(f"  y_test {data['y_test'].shape}")
    print(f"  classes: {np.unique(data['y'])}")
    print("  saved to mnist1d_data.pkl")
