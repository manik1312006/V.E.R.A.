# A Robot Web for Distributed Many-Device Localisation

**Authors:** Riku Murai, Joseph Ortiz, Sajad Saeedi, Paul H. J. Kelly, Andrew J. Davison
**Source:** http://arxiv.org/abs/2202.03314v2

## Abstract

We show that a distributed network of robots or other devices which make measurements of each other can collaborate to globally localise via efficient ad-hoc peer to peer communication. Our Robot Web solution is based on Gaussian Belief Propagation on the fundamental non-linear factor graph describing the probabilistic structure of all of the observations robots make internally or of each other, and is flexible for any type of robot, motion or sensor. We define a simple and efficient communication protocol which can be implemented by the publishing and reading of web pages or other asynchronous communication technologies. We show in simulations with up to 1000 robots interacting in arbitrary patterns that our solution convergently achieves global accuracy as accurate as a centralised non-linear factor graph solver while operating with high distributed efficiency of computation and communication. Via the use of robust factors in GBP, our method is tolerant to a high percentage of faults in sensor measurements or dropped communication packets.