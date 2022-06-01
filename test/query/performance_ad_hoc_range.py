#!/usr/bin/env python3
# Copyright 2022 Unibg Seclab (https://seclab.unibg.it)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import argparse
from email.mime import base
import glob
import os
import re
from collections import defaultdict

import matplotlib.pyplot as plt
import pandas as pd


# Fix font size of the plots
plt.rcParams.update({'font.size': 15})


MARKERS = ["o", "s", "^", "D", "*", "p", "h", "8", "v"]


def compute_statistics(samples, baseline=1):
    df = pd.DataFrame(zip(*samples))
    avg = df.mean(axis=1)
    variance = df.var(axis=1) / len(samples)
    # Compute a single avg and variance assuming they are iid
    return avg.mean() / baseline, variance.mean()


def plot(baseline, curves, path):
    ks, avgs, variances = zip(*curves[0])

    # Baseline
    baseline = plt.plot(ks, [baseline] * len(ks), linestyle="dashed", color="black")
    # Other lines
    lines = []
    for i, curve in enumerate(curves):
        ks, avgs, variances = zip(*curve)
        line = plt.plot(ks, avgs, marker=MARKERS[i], markersize=8)
        lines.extend(line)

    plt.xlabel('k')
    plt.ylabel("#t downloaded / #t in result")
    # Put baseline as the 3rd element in the legend
    current_lines = lines[:1] + baseline + lines[1:]
    current_labels = labels[:1] + ["baseline"] + labels[1:]
    legend = plt.legend(current_lines, current_labels,
                        bbox_to_anchor=(0.23, 1),
                        frameon=False,
                        loc='lower left',
                        prop={'size': 12},
                        ncol=2)
    for handle in legend.legendHandles:
        handle._legmarker.set_markersize(8)
    plt.ylim(bottom=0)
    plt.xticks([10, 25, 50, 75, 100])

    fig = plt.gcf()
    fig.savefig(os.path.join("test/results/query/images/ad-hoc", path),
                bbox_extra_artists=(legend, ),
                bbox_inches='tight')
    if is_interactive: plt.show()
    # Clear the current Figure’s state without closing it
    plt.clf()


parser = argparse.ArgumentParser(
    description='Visualize performance evaluations by K.'
)
parser.add_argument('-i',
                    '--interactive',
                    action='store_true',
                    help='show plots')

args = parser.parse_args()
is_interactive = args.interactive

dirs = [
    "test/results/query/k/range-AGEP",
    "test/results/query/k/range-WAGP",
]

size_curves, size_worsening_curves = [], []
labels = []
for dir in dirs:
    column = dir.split('-', 1)[1]
    print(f"[*] COLUMN: {column}")
    print(os.path.join(dir, f"baseline*.csv"))
    baseline = glob.glob(os.path.join(dir, f"baseline*.csv"))[0]
    print(f"[*] Read baseline: {baseline}\n")
    df_baseline = pd.read_csv(baseline, index_col="index")
    avg_baseline_size = df_baseline["nof_result_tuples"].mean()

    # Group performance evaluation files by configuration
    filenames = []
    for filename in os.listdir(dir):
        match = re.search(r"-latency=\d+ms-gid-kv\.csv", filename)
        if match:
            filenames.append(filename)

    size, size_worsening = {}, {}

    # Group performance evaluation files by K
    by_K = defaultdict(list)
    for filename in filenames:
        match = re.search(r"-K=(\d+)-", filename)
        if match:
            K = int(match.group(1))
            by_K[K].append(filename)

    for K, filenames in by_K.items():
        print(f"[*] K={K}")
        current_size = []
        for filename in filenames:
            evaluation = os.path.join(dir, filename)
            print(f"Read {evaluation}")
            df = pd.read_csv(evaluation, index_col="index")
            current_size.append(df["nof_plaintext_tuples"])

        size[K] = compute_statistics(current_size)
        size_worsening[K] = compute_statistics(current_size, avg_baseline_size)

    size_curves.append([(k, *size[k]) for k in sorted(size.keys())])
    size_worsening_curves.append([(k, *size_worsening[k])
                                  for k in sorted(size_worsening.keys())])
    labels.append(column)

print("[*] Visualize performance overhead")
plot(1, size_worsening_curves, "size-overhead-range-by-K.pdf")
