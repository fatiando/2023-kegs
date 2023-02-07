# Fatiando a Terra: Open-source tools for geophysics

## Authors

[Santiago Soler](https://www.santisoler.com)<sup>1</sup>
[Lindsey J. Heagy](https://lindseyjh.ca/)<sup>1</sup>

> 1. Department of Earth, Ocean and Atmospheric Sciences, University of British
>    Columbia

## Abstract

<!-- a little about the project -->

The Fatiando a Terra project (https://www.fatiando.org) is a collection of
open-source Python libraries for geophysics that covers a wide range of
functionalities, from data download and processing to modelling and inversion.
Each one of the libraries in the project was designed with their own
scope of applications.

Harmonica is focused on processing and modelling gravity and
magnetic data. It provides tools for gravity corrections like Bouguer and
terrain effects; interpolations and upward continuation through equivalent
sources; Fourier domain filters like vertical derivatives, upward continuation
and reduction to the pole; forward modelling of geometries like prisms, point
sources and tesseroids (a.k.a spherical prisms); and more.
Boule hosts reference ellipsoids useful for applying coordinate
conversions and normal gravity calculations.
Verde offers tools for processing and interpolating any type of spatial data
through a diverse set of methods, with a machine learning inspired approach.
Pooch eases the process of downloading and caching data from the web with
a very simple interface. Lastly, Ensaio offers a set of curated open-licensed
datasets useful for teaching, practicing and probing our codes.

The project started in 2010 in South America as a simple Python library as part
of a PhD Thesis, and has since growth to include a global community of
contributors. Its progress has been facilitated by a consistent effort of
meeting the highest standards in software development. Through the adoption of
best practices and a thoughtful design of its tools, the project provides well
tested and well documented code that is easy to use, regardless of the Python
skills of its users. This has led the project to be used in real world
applications like scientific research and geophysical exploration within
industry and academia.

During this talk we'll provide an overview of the tools in the Fatiando
project, demonstrate their functionalities using examples from research and
industry applications, and take a look at some code snippets to showcase its
capabilities and ease of use.
We will also take the opportunity to discuss upcoming developments, our roadmap
for the future and plans for implementing highly requested features.

## About the speaker

Santiago Soler is a Physicist and PhD in Geophysics from Argentina.
His research have always been around potential fields, working mainly on the
development of new methodologies for processing and modelling gravity and
magnetic fields.
Examples of these are the forward modelling of tesseroids (spherical prisms)
with variable densities and the gradient-boosted equivalent sources that allow
to interpolate, grid and upward continue very large datasets of harmonic
fields.
In parallel to his research, he's been one of the core developers of the
Fatiando a Terra project: a collection of open-source Python libraries for
geosciences.
His current role as a Postdoctoral Research Fellow at the University of
British Columbia, under the supervision of Dr. Lindsey Heagy and within the
Geophysical Inversion Facility group, allows him to research on the
characterization of the potential of serpentinized rocks for carbon
sequestration using joint inversions of gravity and magnetic data.
He still has a strong commitment with the open-source geoscientific ecosystem
by contributing to the development of Fatiando a Terra and SimPEG, a Python
framework for geophysical inversions.
