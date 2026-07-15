# Horizon Robotics

Source: https://en.wikipedia.org/wiki/Horizon%20Robotics

Horizon Robotics, Inc. (Chinese: 地平线; pinyin: Dìpíngxiàn) is a Chinese technology company headquartered in Beijing. The company develops artificial intelligence (AI) chips used in self-driving cars and advanced driver assistance systems (ADAS).


== Background ==
Horizon Robotics was founded in 2015 by several former Baidu employees, including Yu Kai, who previously led Baidu's self-driving car division.
The company was funded by notable investors that included Intel, Hillhouse Investment, HongShan, Yuri Milner, Sinovation Ventures and Yunfeng Capital. Other backers include BYD, Chery and CATL. 
In December 2017, Horizon Robotics launched Journey 1.0, the first generation of its AI chips used in vehicles. It would help cars recognize external objects in a low power consumption manner.
Originally Horizon Robotics planned to hold an initial public offering (IPO) in the United States that could raise as much as $1 billion. However, in October 2021, it was reported that it changed its IPO country to Hong Kong instead. This came at a time where the Chinese government was increasing scrutiny of overseas listings.
In October 2022, Volkswagen Group invested $2.3 billion to establish a joint venture (JV) with Horizon Robotics. The JV was named Carizon and was aimed to develop in-house vehicle software for Volkswagen.
At the 2023 World Internet Conference, Yu announced that the number of vehicles featuring navigate on autopilot (NoA) equipped with Horizon Robotics chips has surpassed that of Nvidia. According to a report from China Money Network, Horizon Robotics controlled 49% of the Chinese self-driving chip market in 2023.
In March 2024, Horizon Robotics submitted its IPO application to the Hong Kong Stock Exchange expected to raise $500 million. In October 2024, the offering was priced at the top of its price range raising $696 million.
In January 2025, Horizon Robotics announced its goal of shipping over 10 million chips in 2025.


== Shareholders ==
As of 2024, Horizon Robotics' major shareholders includes (by penetration):

Yu Kai - 75.18%
Huang Chang - 16.95%
Tao Feiwen - 7.35%


== Products ==
While Horizon Robotics mainly focuses on developing AI chips used in the automobile industry, it also develops its Sunrise line of AI chips that are used in surveillance cameras and other internet-connected smart devices. It holds partnerships with Chery, Audi, SAIC Motor and SK Telecom.


=== Journey 2 ===
The Journey 2 was released in 2019, and was the first automotive AI chip made by a Chinese company. It uses Horizon's self-developed Brain Processing Unit (BPU) 2.0 architecture, and is capable of over 4 TOPS of compute performance while consuming 2 watts of power. It has a multicore CPU consisting of ARM Cortex-A53 cores clocked at up to 1.5GHz, 640GB/s internal bandwidth bus,


=== Journey 3 ===
The Journey 3 was released in September 2020. It continues to use the BPU 2.0 architecture and is fabricated on TSMC's 16nm node, now providing 5TOPS while using 2.5 watts of power. Applications include Li Auto One.


=== Journey 5 ===
The Journey 5 uses eight ARM Cortex-A55 in its CPU for 26k DMIPS, and has a GPU capable of 128 TOPS using Horizon's Bayesian BPU architecture. Its ISP is capable of handling 16 HD cameras and supports 4x4 MIPI to support 4K cameras. It is produced on TSMC's 16nm FinFET process node. It received SGS-TÜV's ISO 26262 ASIL-B automotive safety certification in June 2021. Unlike the previous chips in the Journey series, which were primarily used with CNN models, the Journey 5 chips are the first in the series to be optimized for use with Transformer models.


=== Journey 6 ===
The Journey 6 generation of chips was first teased in 2023, with specs of only the top of the line 6P revealed. The full lineup of chips was announced on 25 April 2024, when more details specifications of the 6B, 6E, 6M, and 6P were revealed at the launch presentation. This generation introduces the BPU 3.0 architecture known as Nash, the use of larger ARM Cortex-78AE cores from the high-performance Cortex-A7X series which are capable of out-of-order execution, and 3D GPU visualization using ARM's Mali G78AE architecture rather than using a digital signal processor. According to Horizon, the Nash BPU architecture was designed to handle high-parameter transformer models, and is optimized to run end-to-end architectures. The Journey 6 series integrates the CPU, BPU, GPU, and MCU into a single SoC, increasing performance while reducing cost, power consumption, and simplifying board design. This high degree of integration and hardware simplification allows the Journey 6 to act as a plug-and-play solution, allowing for easy hardware upgrades for automakers and users which Horizon compares to upgrading a desktop PC's graphics card.


==== Journey 6B ====
The Journey 6B was announced on 25 April 2024 and is aimed at entry-level active safety ADAS solutions. Horizon Robotics said that the chip got orders from Tier 1 suppliers Bosch and Denso, along with NavInfo, Furuitech and Youjia Innovation. It is intended to be the successors to the Journey 2 and Journey 3 chips.


==== Journey 6E & 6M ====
The Journey 6E and 6M are positioned as cost effective solutions for highway NOA systems with some urban capabilities. It meets the AEC-Q104 standard and reduces costs and power consumption through high integration. It is intended to be the successors to the Journey 5 chips.
Initial automotive customers include SAIC, Volkswagen Group, BYD, Li Auto, GAC, Deepal, BAIC, Chery, Exeed Sterra, and Voyah, and Tier 1 customers include Bosch, Luxshare, Huaqin, and TzTek, with interest shown from Continental, Denso, Valeo, and ZF.


==== Journey 6P ====
The Journey 6P is the most powerful chip design by Horizon Robotics to date, and is intended for high-end full-scenario NOA solutions. The chip contains 37 billion transistors and is fabricated on TSMC's 7nm, and contains a 18-core CPU capable of 410k DMIPS, is capable of 560 TOPS from its 4 Nash BPU cores, and uses LPDDR5x‑8533 RAM for a total of 204 GB/s of bandwidth. It has an ISP with 24 channels capable of processing 4K video or other sensors including up to 18MP front-facing cameras, mmWave radar and LiDAR data.
Mass production of the 6P is expected to start in the third quarter of 2025.


=== Journey 7 ===
In March 2026, Horizon announced plans for the Journey 7 family of chips, which is expected to arrive in 2027. Compared to their previous chip generations like the Journey 6, the design is led by the algorithm team's needs rather than the chip design team to better match . It will use Horizon's fourth generation BPU architecture named Riemann. Horizon says that the top chip in the family, the J7P, aims to significantly surpass the performance of the 1000 TOPS Nvidia Thor-X and compete with Tesla's upcoming AI5 chip, which is rumored to have around 2000–2500 TOPS of performance.


=== Carizon C7H ===
In March 2026, Horizon's joint venture with Volkswagen, known as Carizon (sytlized 'CARIZON') announced that it was developing the C7H chip. Development is primarily being done by Carizon itself, with some support from CARIAD and Horizon. It is based on Journey 7 family and uses the Riemann BPU architecture, will be fabricated on a 4nm or 3nm process node, and will have a per-chip performance of around 500–700 TOPS. It is intended to be used in Volkswagen's vehicles using the CEA architecture codeveloped with XPeng.


== See also ==
Yinwang (Huawei's autonomous driving solution company)
Momenta (autonomous driving solution company backed by SAIC, GM, and Toyota)
Qianli Technology (Geely's autonomous driving solution company)
Zhuoyu Technology (FAW and DJI's autonomous driving solution company)
DeepRoute.ai (autonomous driving solution company backed by GWM)
Black Sesame Technologies
Self-driving car
Automobile industry in China
Semiconductor industry in China


== References ==


== External links ==
Official website