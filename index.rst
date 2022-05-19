:tocdepth: 1

.. sectnum::

Abstract
========

:abbr:`HiPS (Hierarchical Progressive Survey)` is an `IVOA-standard protocol <https://ivoa.net/documents/HiPS/20170519/REC-HIPS-1.0-20170519.pdf>`__ for providing a hierarchical, pre-rendered view of sky survey data.
It is one of the ways in which Rubin Observatory will make available its survey data to data rights holders.
This tech note describes the implementation strategy for the Rubin Science Platform HiPS service.

Overview
========

A HiPS data set is a pre-generated tree of image files and accompanying metadata from a sky survey.
It is structured to support exploration of images taken from a survey, often through panning and zooming via an interactive HiPS client such as `Aladin <https://aladin.cds.unistra.fr/aladin.gml>`__.
The HiPS naming structure is designed to allow one-time generation of a static, read-only tree of files that provide the HiPS view of a survey.
Those files can be served by any static web server without requiring a web service.
The client is responsible for providing any desired user interface and for choosing which images to retrieve, done via algorithmically constructing URLs under a base HiPS URL and then requesting the corresponding file from the server.

Most HiPS data collections are public and therefore do not require authentication.
However, for Rubin Observatory, the full HiPS data set will be available only to data rights holders and will therefore require authentication.

We do not expect to frequently update the HiPS data set.
Instead, during a data release, we will generate the HiPS data set for that release, and then serve that data set for users of that data release.
In the future, we may want to multiple versions of the HiPS data set at different URLs, corresponding to different data releases.
This is not part of the initial implementation, but can be easily added in the future.

URL
===

For DP0.2, we will use ``/api/hips`` as the root URL for the HiPS tree.

In the future, we will rework the URL structure for the Rubin Science Platform to use separate domains for separate aspects and services provided by the platform.
This allows isolation between services by moving them into separate trust domains, and is discussed at length in `SQR-051`_.

.. _SQR-051: https://sqr-051.lsst.io/

Once that work is done, HiPS (like many other services) will move to its own domain.
The long-term approach will require generating a separate authentication cookie specifically for HiPS (see :ref:`the Google Cloud Storage design <gcs-service>`), so that domain will not be shared with other services and will probably be something like ``hips.api.<domain>`` where ``<domain>`` is the parent domain of that deployment of the Rubin Science Platform (such as ``data.lsst.cloud``).
At that time, we will also add a way of distinguishing between HiPS trees for different data releases, either by adding the data release to the domain or as a top-level path element in front of the HiPS path, whichever works best with the layout of the underlying storage and the capabilities of Google CDN.

.. _storage:

Storage
=======

The HiPS data set will be stored in a Google Cloud Storage bucket.
The object names in the bucket will match the paths required by the HiPS standard, and the bucket will only contain the HiPS data set.
When we generate a new HiPS data set, such as for a new data release, we will create a new Google Cloud Storage bucket to hold that new data set.

This decision assumes that the HiPS data will be small enough or the price of Google Cloud Storage will be sufficiently low that it's reasonable to store the HiPS data there.

Options considered
------------------

There are two main options for where to store HiPS data.

POSIX file system
^^^^^^^^^^^^^^^^^

The most commonly-used tools to generate a HiPS data set assume they will be run in a POSIX file system.
One option would therefore be to leave the HiPS data in the file system where it was generated and serve it from there.
This would make it easier to serve the HiPS data using a static file web server (see :ref:`Web service <web-service>`).
It is the natural storage anticipated by the HiPS standard.

However, using a POSIX file system would lock us into running our own service to serve the data, since there is no standard Google service to serve data from a POSIX file store.
In general, POSIX file systems are second-class citizens in a cloud computing environment, and object stores are preferred and have better service support.
In Google Cloud in particular, it's harder to manage multiple POSIX file stores than it is to manage multiple Google Cloud Storage buckets.
While we will need a POSIX file system to provide home directory space for interactive users, we would prefer to minimize our use beyond that.
For example, we expect the primary repository for each data release to be an object store.

Google Cloud Storage
^^^^^^^^^^^^^^^^^^^^

As mentioned above, this is our preferred repository for project data that is stored in the cloud (and HiPS data is sufficiently small that cloud storage for it should be reasonable).
Google also supports serving data directly out of Google Cloud Storage, which should allow us to eliminate our web service in the future, instead serving data directly from the GCS bucket, augmented with a small bit of code to check user authentication.  (See :ref:`Web service <web-service>` for more details.)

This also allows us to easily create new GCS buckets for each release of HiPS data, easily manage the lifecycle of older or test versions of the HiPS data, and choose appropriate storage (for both cost and redundancy) to fit the requirements of HiPS data, rather than the more stringent requirements for interactive POSIX file systems.

The drawback of this approach is that we must either use Google's ability to serve data directly from Google Cloud Storage, or we have to write a web application to serve the data.

.. _web-service:

Web service
===========

For the immediate requirement of a HiPS service for the DP0.2 data preview release, we will use a small `FastAPI <https://fastapi.tiangolo.com/>`__ web service that retrieves data from the Google Cloud Storage bucket.
In the longer term, we will switch to serving the HiPS data sets directly from Google Cloud Storage buckets, using helper code (probably via Cloud Run) to set up authentication credentials.

Options considered
------------------

There are three major technologies that could be used to serve the HiPS data, and a few options within those that we considered.

NGINX
^^^^^

The HiPS standard is designed for serving the data set using an ordinary static file web server.
NGINX is already used by the Rubin Science Platform, and using NGINX to serve the data has the substantial advantage that static file web servers are very good at quickly serving static files with all the protocol trappings that web browsers expect.
For example, they will automatically provide ``Last-Modified`` and ``ETag`` headers, handle ``If-None-Match`` cache validation requests correctly, and use the operating system buffer cache to speed up file service.

However, in the Rubin Science Platform environment, there are several serious drawbacks.

The Science Platform is Kubernetes-native and does not use a traditional web server configured to serve from a POSIX file system at any other point, nor is it expected to in the future.
Using a web server such as `NGINX <https://www.nginx.com/>`__ still requires running it as a separate deployment specific for HiPS.
This is also not a common configuration for NGINX in a Kubernetes environment (as opposed to using NGINX as an ingress web server, which we already do, but which does not serve static files).
This would require finding an appropriate container, configuring it for our purposes, and keeping it up to date with new NGINX releases, since NGINX is an active target of attacks).

Using this approach also requires the files live in a POSIX file system that's mounted into the NGINX pod.
As mentioned above, we would prefer to use Google Cloud Storage as the default storage mechanism for project data.
That also means this is not a stepping stone towards serving the data directly from Google Cloud Storage, which is the best long-term solution (as discussed below).

Finally, this approach requires writing and maintaining NGINX configuration, which introduces a new pseudo programming language.

.. _gcs-service:

Google Cloud Storage
^^^^^^^^^^^^^^^^^^^^

The best service is one that we don't have to write or maintain and can instead enable with simple configuration.
Here, that's serving the data directly out of Google Cloud Storage.
If, like other astronomy sky surveys, our HiPS data set was public, this would be the obvious approach.
Google Cloud Storage is extremely good (and fast) at static file web service from a GCS bucket and supports all the caching and protocol details we could desire.

Unfortunately, our HiPS data set requires authentication, which means that Google Cloud Storage is not suitable out of the box.

Our authentication is done with bearer tokens specific to each Rubin Science Platform deployment (see `DMTN-193`_).
This is normally handled by the ingress for that Science Platform deployment, which sits in front of all Science Platform services and can uniformly apply the security and access policy.
Serving data directly from Google Cloud Storage would be done from the Kubernetes cluster and thus would not go through the ingress, and would therefore have to us a separate mechanism to set appropriate authentication credentials after login and to check those authentication credentials.

.. _DMTN-193: https://dmtn-193.lsst.io/

Google does provide a mechanism to support this by `combining Cloud Load Balancing, Cloud CDN, and Cloud Run <https://cloud.google.com/community/tutorials/securing-gcs-static-website>`__.
Here is what that architecture would look like in diagram form.

.. figure:: /_static/gcs.png
   :name: Google Cloud Storage architecture

   Google Cloud Storage architecture

If the user were not authenticated, the load balancer would route the user to a URL backed by the login helper Cloud Run function.
It in turn would redirect the user to Gafaelfawr in the appropriate cluster for authentication.
On return from that redirect, it would set a signed cookie for the CDN.
The load balancer would recognize that cookie and pass subsequent requests through to the CDN, which would verify the cookie and then serve files directly from Google Cloud Storage.

We've not used this approach for the Science Platform before, and this login approach would benefit considerably from the multi-domain authentication approach proposed in `SQR-051`_ but not yet implemented.
It's therefore not the most expedient choice to get a HiPS service up and running for DP0.2 and public testing.

This appears to be the best long-term approach, with the best security model and the smallest amount of ongoing code or service maintenance, but will require more work to implement.

Web service
^^^^^^^^^^^

Writing a small web service to serve data from Google Cloud Storage is the simplest approach, since we have a well-tested development path for small web services and such a service can use the authentication and access control facilities provided by the Kubernetes ingress.
This is the approach that we decided to take for the short-term DP0.2 requirement.

There are a few drawbacks to this approach.
The first is performance: rather than serving the data through the highly-optimized and highly-efficient Google frontend, or even the less-optimized but still efficient NGINX static file service, every request will have to go through a Python layer.
However, the additional delay will likely not be significant for early testing.

The second drawback is the complexity that has to be implemented manually in Python.
Static file web servers do a lot of protocol work that has to be reproduced manually: providing metadata for caching, responding to cache validation requests, mapping files to proper MIME media types, sanitizing path names to protect against security exploits, and scaling.
This required a couple of days of implementation work and potentially will require more debugging and maintenance going forward.
This is part of the reason for preferring use of Google Cloud Storage directly in the longer term.

As discussed in :ref:`Storage <storage>`, the data could be served from either a Google Cloud Storage bucket or a POSIX file system.
The POSIX file system approach would be simpler since it would permit use of standard static file server modules in Python web frameworks.
However, for the reasons stated there, we chose Google Cloud Storage as the storage backend.

Given that, there are two ways to serve the files:

#. Stream the file from Google Cloud Storage through the web service to the client.
   This adds more latency, load, and network traffic because the file in essence has to cross the network twice: once from GCS to the Kubernetes cluster and then again to the client.
   It also requires Python code sit in the middle of the network transaction and pass the bytes down to the client.

#. Redirect the client to a signed URL that allows them to download the file from Google Cloud Storage directly.
   This is more efficient, since generating the signed URL doesn't require a Google API call and Google Cloud Storage itself then serves the file.
   However, it inserts a redirect into the protocol flow, which may confuse some HiPS clients, and it means that the URL a user would see in a web browser is a long, opaque blob with the Google signature attached.

Either approach would work, but since the goal of the initial implementation was expediency for testing, the second option raised more unknown factors, and we expect to replace it with an approach using Google Cloud Storage directly, we chose the first option as the simplest approach.

We implemented this approach via a small, generic static file web server backed by Google Cloud Storage called `crawlspace`_.

.. _crawlspace: https://github.com/lsst-sqre/crawlspace/

Here is what this architecture looks like in diagram form.

.. figure:: /_static/web-service.png
   :name: Web service architecture

   Web service architecture

crawlspace tells clients (via the ``Cache-Control`` header) that all files can be cached for up to an hour.
This is relatively short for testing purposes.
We will likely increase that for the eventual production service, since we expect HiPS files to be static once generated.

crawlspace attempts to support browser caching by passing through the ``Last-Modified`` and ``ETag`` headers from the underlying Google Cloud Storage blob metadata, and implementing support for ``If-None-Match`` to validate the cache after the object lifetime has expired.

References
==========

`crawlspace`_
    The crawlspace static file web service backed by Google Cloud Storage.

`DMTN-193`_
    General overview and discussion of web security concerns for the Rubin Science Platform.

`IVOA HIPS 1.0`_
    The current standard for the HiPS protocol, dated May 19th, 2017.

`Securing static GCS web site`_
    Google tutorial on how to secure a static web site using Cloud Run to manage the login flow.

`SQR-051`_
    Proposed design for improving web security of the Rubin Science Platform.
    Relevant to this document, it advocates for using separate domains for separate aspects or services of the Science Platform for better trust isolation.

.. _IVOA HIPS 1.0: https://ivoa.net/documents/HiPS/20170519/REC-HIPS-1.0-20170519.pdf
.. _Securing static GCS web site: https://cloud.google.com/community/tutorials/securing-gcs-static-website
