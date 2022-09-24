#!/usr/bin/env python3

import HeapsPlots
import ZipfPlots

if __name__ == "__main__":
    output_dir = "./figures"
    ZipfPlots.main("data.txt", output_dir, format="pdf")
    HeapsPlots.main("./results/heaps.csv", output_dir)
