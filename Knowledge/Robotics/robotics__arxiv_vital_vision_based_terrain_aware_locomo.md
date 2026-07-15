# ViTAL: Vision-Based Terrain-Aware Locomotion for Legged Robots

**Authors:** Shamel Fahmi, Victor Barasuol, Domingo Esteban, Octavio Villarreal, Claudio Semini
**Source:** http://arxiv.org/abs/2212.01246v1

## Abstract

This work is on vision-based planning strategies for legged robots that separate locomotion planning into foothold selection and pose adaptation. Current pose adaptation strategies optimize the robot's body pose relative to given footholds. If these footholds are not reached, the robot may end up in a state with no reachable safe footholds. Therefore, we present a Vision-Based Terrain-Aware Locomotion (ViTAL) strategy that consists of novel pose adaptation and foothold selection algorithms. ViTAL introduces a different paradigm in pose adaptation that does not optimize the body pose relative to given footholds, but the body pose that maximizes the chances of the legs in reaching safe footholds. ViTAL plans footholds and poses based on skills that characterize the robot's capabilities and its terrain-awareness. We use the 90 kg HyQ and 140 kg HyQReal quadruped robots to validate ViTAL, and show that they are able to climb various obstacles including stairs, gaps, and rough terrains at different speeds and gaits. We compare ViTAL with a baseline strategy that selects the robot pose based on given selected footholds, and show that ViTAL outperforms the baseline.