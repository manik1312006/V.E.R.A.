# Automatic Layout Generation with Applications in Machine Learning Engine Evaluation

**Authors:** Haoyu Yang, Wen Chen, Piyush Pathak, Frank Gennari, Ya-Chieh Lai
**Source:** http://arxiv.org/abs/1912.05796v1

## Abstract

Machine learning-based lithography hotspot detection has been deeply studied recently, from varies feature extraction techniques to efficient learning models. It has been observed that such machine learning-based frameworks are providing satisfactory metal layer hotspot prediction results on known public metal layer benchmarks. In this work, we seek to evaluate how these machine learning-based hotspot detectors generalize to complicated patterns. We first introduce a automatic layout generation tool that can synthesize varies layout patterns given a set of design rules. The tool currently supports both metal layer and via layer generation. As a case study, we conduct hotspot detection on the generated via layer layouts with representative machine learning-based hotspot detectors, which shows that continuous study on model robustness and generality is necessary to prototype and integrate the learning engines in DFM flows. The source code of the layout generation tool will be available at https://github. com/phdyang007/layout-generation.