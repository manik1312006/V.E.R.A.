# Partial observations and conservation laws: Grey-box modeling in biotechnology and optogenetics

**Authors:** Robert J. Lovelett, Jose L Avalos, Ioannis G. Kevrekidis
**Source:** http://arxiv.org/abs/1909.04234v1

## Abstract

Developing accurate dynamical system models from physical insight or data can be impeded when only partial observations of the system state are available. Here, we combine conservation laws used in physics and engineering with artificial neural networks to construct "grey-box" system models that make accurate predictions even with limited information. These models use a time delay embedding (c.f., Takens embedding theorem) to reconstruct effect of the intrinsic states, and can be used for multiscale systems where macroscopic balance equations depend on unmeasured micro/meso scale phenomena. By incorporating physics knowledge into the neural network architecture, we regularize variables and may train the model more accurately on smaller data sets than black-box neural network models. We present numerical examples from biotechnology, including a continuous bioreactor actuated using light through optogenetics (an emerging technology in synthetic biology) where the effect of unmeasured intracellular information is recovered from the histories of the measured macroscopic variables.