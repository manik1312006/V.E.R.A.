# ReSet: Learning Recurrent Dynamic Routing in ResNet-like Neural Networks

**Authors:** Iurii Kemaev, Daniil Polykovskiy, Dmitry Vetrov
**Source:** http://arxiv.org/abs/1811.04380v1

## Abstract

Neural Network is a powerful Machine Learning tool that shows outstanding performance in Computer Vision, Natural Language Processing, and Artificial Intelligence. In particular, recently proposed ResNet architecture and its modifications produce state-of-the-art results in image classification problems. ResNet and most of the previously proposed architectures have a fixed structure and apply the same transformation to all input images. In this work, we develop a ResNet-based model that dynamically selects Computational Units (CU) for each input object from a learned set of transformations. Dynamic selection allows the network to learn a sequence of useful transformations and apply only required units to predict the image label. We compare our model to ResNet-38 architecture and achieve better results than the original ResNet on CIFAR-10.1 test set. While examining the produced paths, we discovered that the network learned different routes for images from different classes and similar routes for similar images.