# Planning for robotic exploration based on forward simulation

**Authors:** Mikko Lauri, Risto Ritala
**Source:** http://arxiv.org/abs/1502.02474v2

## Abstract

We address the problem of controlling a mobile robot to explore a partially known environment. The robot's objective is the maximization of the amount of information collected about the environment. We formulate the problem as a partially observable Markov decision process (POMDP) with an information-theoretic objective function, and solve it applying forward simulation algorithms with an open-loop approximation. We present a new sample-based approximation for mutual information useful in mobile robotics. The approximation can be seamlessly integrated with forward simulation planning algorithms. We investigate the usefulness of POMDP based planning for exploration, and to alleviate some of its weaknesses propose a combination with frontier based exploration. Experimental results in simulated and real environments show that, depending on the environment, applying POMDP based planning for exploration can improve performance over frontier exploration.