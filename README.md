# Fatiando a Terra: Open-source tools for geophysics

## Abstract

<!-- a little about the project -->

The Fatiando a Terra project (https://www.fatiando.org) is a collection of
open-source Python libraries for geophysics that cover a range of
functionalities, from data download and processing to modelling and inversion.

The history of this project started in 2010 in South America as a simple Python
library as part of a PhD Thesis. Over time, Fatiando a Terra grew and the team
of developers matured and established best practices for maintaining software
projects in the open. At the same time, a community began to form around this
project what heavily encouraged its development, while contributors from
around the world started getting involved through active participation.

Since 2018, the code base has been restructured in order to obtain a better
infrastructure with the emerging geophysical ecosystem. It was split in smaller
libraries, each one with a specific set of goals and scope of applications.
Currently the project host libraries like Verde, for data processing and
interpolations; Pooch, for data downloading and caching; Boule, for managing
reference ellipsoids and compute normal gravity; Harmonica, processing and
modelling gravity and magnetics; and Ensaio that offers a set of curated open
datasets to teach and practice.

The project is notable for meeting the highest standards in software
development. Through the application of best practices and a thoughtful design
of its tools, it provides well tested and well documented code that is easy to
use, regardless of the Python skills of its users.
The high quality of these Python libraries allows other projects and scientists
to rely on them as part as their own code, to conduct their research and also
to develop new methodologies based on these tools.

The Fatiando a Terra libraries are being used worldwide for teaching,
performing scientific research, inside the industry, and also as dependencies
of other software packges: like Pooch that is being used by projects like SciPy
and scikit-image, among others.

<!-- What do we want to show? More geophyiscal oriented -->

During this talk we will introduce the project, its libraries and their
capabilities. We will also showcase how we can use them for processing gravity
and magnetic real world data, relying as well on the existing tools available
in the scientific open-source Python ecosystem.
