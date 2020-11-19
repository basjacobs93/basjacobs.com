---
title: Image Triangulation with Julia
author: Bas
date: '2020-11-18'
slug: image-triangulation-with-julia
---

I have always been fascinated by computer generated art. Recently, I came across the paper [Stylized Image Triangulation](https://cgl.ethz.ch/Downloads/Publications/Papers/2018/Law18a/Law18a.pdf) by Kai Lawonn and Tobias Günther. In this paper, the authors perform image triangulation (approximating an image by tessellation with triangles) by coming up with an initial grid and performing gradient descent. They achieve beautiful triangulations that capture the original images very well. Their code is a combination of MatLab and C++, and is [available on github](https://github.com/tobguent/image-triangulation).
  
As a fun exercise in Julia, I implemented part of their method in a Pluto notebook (like a Jupyter notebook but especially for Julia, see [here](https://github.com/fonsp/Pluto.jl)). My notebook is [available on Github](https://github.com/basjacobs93/image_triangulation).  

## Summary of method
In the paper, the authors start with an initial grid of points that defines a triangulation. This grid can either be a _regular layout_, in which the points are spaced evenly across the width and height of an image, or it can be made via _importance sampling_, in which 'important' regions of the image are found and points are sampled, weighted by this importance. Every triangle gets a constant color, calculated as the mean of the colors of its interior points in the original image.

As an example, consider this image of a beautiful bird called a _Bearded reedling (Panurus biarmicus)_, taken from [this YouTube video](https://www.youtube.com/watch?v=i8YPjJSuse0).

![Bearded Reedling](/post/2020-11-18-image-triangulation-with-julia_files/baardman_2.png)

The two types of initial triangulation are the regular layout (in this case with 50 triangles),

![Bearded Reedling (Regular Layout)](/post/2020-11-18-image-triangulation-with-julia_files/baardman_2_regular_layout.png)
and the triangulation based on importance sampling (in this case by sampling 50 points).
![Bearded Reedling (Importance Sampling)](/post/2020-11-18-image-triangulation-with-julia_files/baardman_2_importance_sampling.png)

Starting with such a triangulation, the triangles are improved iteratively by gradient descent. For every point, a small change in the horizontal and vertical direction is tried, and a gradient is calculated by calculating the errors of the point's adjacent triangles for each such configuration. The error of a triangle is defined as the mean of the differences of its interior points' colors, compared to the original image. This way, the initial triangulation gets better every step, but it may converge to a local optimum, depending on the initial triangulation.  

On top of gradient descent, every couple of steps, every triangle can be split into three by placing an additional point at its centroid. This way, large triangles that have a big error can be split up into smaller triangles with different colors and smaller errors. The triangles eligible for this splitting have to be large enough, should not be too narrow, and should have a large error. These thresholds, together with the number of steps, step size, and other parameters can be tweaked in the code, yielding different results.  

An example output is the below, in which the initial grid was a regular layout, and which resulted in an image of 700 triangles.
![Bearded reedling after optimization (700 triangles)](/post/2020-11-18-image-triangulation-with-julia_files/baardman_2_700.png)

For a more mathematically thorough explanation, I refer to the original paper.  

Coding this in Julia was straightforward, but the performance is not as good as I hoped it would be. Generating the above image took a couple of minutes. The authors of the paper wrote parts of their code in C++ because of performance, and parallelized and optimized the code such that it was faster. Although Julia is fast, my naive implementation still requires lots of loops (over the triangles, points, pixels), so it makes sense for it to be slow.

## More results

Another beautiful picture of the same species of bird is the following ([source](https://commons.wikimedia.org/wiki/File:Bartmeise(Cropped)_by_Wolfram_Riech.jpg) by _Kaeptn chemnitz, [CC BY 3.0](https://creativecommons.org/licenses/by/3.0), via Wikimedia Commons_).

![Bearded reedling (source: wikimedia)](/post/2020-11-18-image-triangulation-with-julia_files/baardman.png)

The resulting triangulations are more abstract than the above, but I think they are beautiful. The results with 100, 500 and 1000 triangles are below.

<img src="/post/2020-11-18-image-triangulation-with-julia_files/baardman_100.png" alt="Bearded reedling (100 triangles) "/>
<img src="/post/2020-11-18-image-triangulation-with-julia_files/baardman_500.png" alt="Bearded reedling (500 triangles)"/>
<img src="/post/2020-11-18-image-triangulation-with-julia_files/baardman_imp_1000.png" alt="Bearded reedling (1000 triangles)"/>

## Conclusion

Implementing part of the methodology of the paper was fairly straightforward in Julia, even though my experience with the language is limited. However, the resulting code was not as fast as I would've liked. This makes it hard to fiddle around with the parameters, since a lot of time is spent waiting for the results. Some more focus on efficiency is needed to speed things up. That said, even though my implementation is naive, a pretty triangulation is only a key-press away and can be generated in a couple of minutes.  

As stated, the notebook is available [on GitHub](https://github.com/tobguent/image-triangulation), so feel free to try it out!
