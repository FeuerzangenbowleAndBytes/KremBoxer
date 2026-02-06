Methods
==========

The primary purpose of the KremBoxer code is to process the raw sensor data from the dualband KremBoxes into Fire Radiative Power (FRP) time traces.  This page will describe
the physics and algorithms involved in calibrating the devices and obtaining FRP estimates.

Physics
----------

The dualband Kremboxes measure the amount of IR radiation observed in
two bands (roughly 1-6 um and 8-14 um).  We can use the power measured in these two bands to obtain the total power emitted
as radiation from a fire (Fire Radiative Power, FRP) by modeling the fire with blackbody physics.

The Planck equation describes the spectral radiance of a blackbody as a function of temperature and wavelength:

.. math::
    B(\lambda, T) = \frac{2hc^2}{\lambda^5}\frac{1}{e^{\frac{hc}{\lambda k_B T}}-1}

where :math:`B` is the spectral radiance, :math:`\lambda` is the wavelength, :math:`T` is the temperature, :math:`h` is Planck's constant, :math:`c` is the speed of light, and :math:`k_B` is Boltzmann's constant.
The spectral radiance in measured in units of  :math:`\frac{W}{sr \cdot m^2 \cdot m}` and describes the amount of power emitted per unit area per unit solid angle per unit wavelength.  Planck's equation
strictly applies to a blackbody, which is an idealized object that absorbs all radiation incident upon it.

The spectral radiance of a real object is given by the Planck equation multiplied
by the emissivity of the object which may also depend on wavelength and temperature.  The emissivity ranges from 0 to 1, and in this work we will use
the greybody approximation which assumes that the emissivity is a simple constant, :math:`\epsilon(\lambda, T)=\epsilon`.  The spectral radiance for a greybody is then:

.. math::
    B^{GB}(\lambda, T) = \epsilon B(\lambda, T)

How much of this power reaches the detector?  The detector has a field of view (FOV) which is the solid angle over which it can detect radiation.
Let's suppose the FOV is a cone with a half-angle of :math:`\theta_D`.  The detector will only detect radiation from the fire that is within this cone.
Furthermore, it may be that only a fraction, :math:`A`, of the detector FOV is actually occupied by fire.  Since the radiation emitted by the background
is small compared to the fire, we can model the total power at a particular wavelength incident on the detector as the integral of the spectral radiance over the FOV
times the fraction of the FOV occupied by fire:

.. math::
    W^{GB}(\lambda, T) = A \cdot \int_{0}^{2\pi} d\phi \int_{\frac{\pi}{2}-\theta_D}^{\frac{\pi}{2}} cos \theta \cdot sin \theta \cdot d\theta \cdot B^{GB}(\lambda, T)

Since the Planck equation does not depend on angle, the result of this integral is just a constant, :math:`\Omega(\theta_D)`, parameterized by :math:`\theta_D`:

.. math::
    W^{GB}(\lambda, T) = \epsilon A \Omega(\theta_D) B(\lambda, T)

Note that in the case where the FOV is an entire half-hemisphere, :math:`\theta_D=\frac{\pi}{2}`, then :math:`\Omega(\theta_D)=\pi`.

:math:`W^{GB}(\lambda, T)` describes the power incident on the detector, but only some wavelengths are actually detected depending on the sensor's
bandpass, :math:`F(\lambda)`, which describes the fraction of radiation at each wavelength that gets through each sensor's filter. So, in order
to compute the total radiance detected by the sensor, we must integrate :math:`W^{GB}(\lambda, T)` over the bandpass:

.. math::
    W^{GB,D}(T) = \int_0^\infty W^{GB}(\lambda, T) F(\lambda) d\lambda = \epsilon A W^D (T)

    W^D (T) =  \Omega(\theta_D) \int_0^\infty B(\lambda, T) F(\lambda) d\lambda

where :math:`W^{GB,D}(T)` is the power detected by the sensor and :math:`W^D (T)` is the power detected by the sensor if the target were a perfect blockbody that covered the entire FOV.

