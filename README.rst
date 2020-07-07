====
brig
====

Conceptually, an offspring of Torb, but following a different path.

.. Important::

  This repository is a work in progress. Its primary function is to support work at 4DN-DCIC,
  but even within that group, it does not supplant the Torb function at this time.
  The hope is that it will grow up to do that.

Overview
========

This repo provides a place to lock away source code for lambda functions,
so they can be under source control and we can have additional tests and
supporting information that has no place in the AWS lambda function
interface.

Goals
-----

Not all of the goals of this repo are yet realized, though some are.

* A place to store lambda function sources under version control.

  Status: Implemented.

  This was the initial need that created this repo, but it does not
  exhaust the set of needs we'd like to accomplish.

* A place to declare build configurations and produce uploadable bundles.

  Status: Implemented

* A place to test lambda functions before deploying them.

  Status: Basic testing implemented.

  You can set up tests here, but they don't yet integrate with other tests on AWS.

* A way to automate uploads to AWS.

  Status: Not yet implemented.

* A command line interface to invoke AWS functions.

  Status: Not yet implemented.

Setting up scripts
------------------

It is recommended, though not required, that you put the ``bin`` folder on your PATH,
as in::

    export PATH=/path/to/brig/scripts:$PATH

This will make the following scripts available:

* ``brig-build`` will build a zip file for upload.

* ``brig-test`` will test a brig function to see if it's ready for upload.
  This is the same as::

    brig-build --testonly


Using brig-build to package a Lambda Function zip file for upload
-----------------------------------------------------------------

You can 'build' a function by using the ``brig-build`` command with your working directory set
to the folder of any function. See `File Structure`_ below for details.

Building needs these prerequisites:

* The ``src/`` folder will be taken as the source to be built. It should not include requirements.

* The ``requirements.txt`` can specify any requirements.
  When staged, they will be staged in the same folder as the source file(s).

Building will accomplish these actions:

* Any existing ``stg/`` file will be cleaned out, or if one does not exist, ``stg/`` will be created.

* Sources will be copied from ``src/`` to ``stg/``.

* Requirements, if a ``requirements.txt`` file exists, will be installed in the same ``stg/`` folder.

* A zip file of ``stg`` will be produced in ``builds/`` with a unique name and ``builds/staged`` will be linked to it.

* Tests, if a ``scripts/test`` file exists, will be invoked, giving the name of the ``stg`` folder
  as a command line argument, so that the script can prepend it. (This allows testing other folders
  with the same script if needed.)

* If tests pass, or if there were no tests, any existing ``builds/current`` will be renamed ``builds/previous``
  and a new ``buids/current`` will be made to link to the same file that ``builds/staged`` points to.

  Notes:

  * Any prior ``builds/previous`` link will be lost, though the underlying target of that link will be unaffected.
  * ``builds/current`` and ``builds/staged`` point to the same file only if testing succeeds.


Uploading Your Lambda Function
------------------------------

You'll need to upload the zip file to corresponding ``Lambda > Functions > {function-name}`` page yourself.
A script to do this is planned but does not yet exist.


File Structure
==============

If you want to add to this repo, please claim a subfolder of brig/apis named for an API (or
similar set of related functions that you just want to group together that way), as in::

    brig/
    |
    +-- LICENSE
    +-- README.rst
    +-- scripts/
    |   |
    |   +-- brig-build  <-- a script that will build any function if invoked from its folder
    |   :                   with the recommended file structure.
    |
    +-- apis/
    |   |
    |   +-- api-1/
    |   |   |
    |   |   +-- README.rst  <-- Info about purpose, scripts, code review, etc. for api-1.
    |   |   |
    |   |   +-- functions/
    |   |   |   |
    |   |   |   +-- function-1/
    |   |   |   |   |
    |   |   |   |   requirements.txt   <-- requirements needed by files in src/
    |   |   |   |   |                      (loaded automatically by brig-build)
    |   |   |   |   +-- scripts/       <-- utility scripts to help manage function-1
    |   |   |   |   +-- src/           <-- your source code for function-1
    |   |   |   |   +-- tests/         <-- test code for function-1
    |   |   |   |   +-- stg/           <-- (not for checkin) reserved staging area for building zips of function-1
    |   |   |   |   +-- builds/        <-- (not for checkin) a local history of builds done
    |   |   |   |   |   +-- current    <-- a symbolic link to the current build
    |   |   |   |   |   +-- previous   <-- a symbolic link to the preious build
    |   |   |   |   |   +-- staged     <-- a symbolic link to the latest candidate build
    |   |   |   |   |   |                  (linked the same as 'current' IFF testing succeeds)
    |   |   |   |   |   :
    |   |   |   |
    |   |   |   +-- function-2/
    |   |   |   +-- function-3/
    |   |   |   :
    |   |   :
    |   +-- api-2/
    |   +-- api-3/
    |   :
    |
    +---functions/                     <-- (see explanation below)


Or else if you have an isolated function, put it in brig/functions.
(You can move it to an API later if you need to), as in::

    brig/
    |
    +-- LICENSE
    +-- README.rst
    +-- ...more globally shared stuff...
    |
    +-- functions/
    |   |
    |   +-- function-1/
    |   |   |
    |   |   +-- requirements.txt       <-- requirements needed by files in src/
    |   |   |                              (loaded automatically by brig-build)
    |   |   +-- scripts/               <-- utility scripts to help manage function-1
    |   |   +-- src/                   <-- your source code for function-1
    |   |   +-- tests/                 <-- test code for function-1
    |   |   +-- stg/                   <-- (not for checkin) reserved staging area for building zips of function-1
    |   |   +-- builds/                <-- (not for checkin) a local history of builds done
    |   |   |   +-- current            <-- a symbolic link to the current build
    |   |   |   +-- previous           <-- a symbolic link to the preious build
    |   |   |   +-- staged             <-- a symbolic link to the latest candidate build
    |   |   |   |                          (linked the same as 'current' IFF testing succeeds)
    |   |   |   :
    |   |
    |   +-- function-2/
    |   +-- function-3/
    |   :
    |
    +-- apis/                          <-- (see explanation above)


.. Note::

  You don't have to follow the structure here for your own folder,
  as long as you put a ``README.rst`` in that folder explaining your policy.


Code Review
===========

Think of the function or API folders you make as light-weight repositories,
so we don't need a million repositories, one per lambda function.
So you don't need to coordinate changes with things in other folders,
and you should do separate versioning of your own area if that's appropriate.
But you should document your code review policy in the ``README.rst``
for your folder.


Etymology
=========

Named for `Brigitte <https://overwatch.gamepedia.com/Brigitte>`_,
daughter of `Torbjörn <https://overwatch.gamepedia.com/Torbj%C3%B6rn_Lindholm>`_
(namesake of our 4DN-DCIC `torb <https://github.com/4dn-dcic/torb>`_ repo).

The name is also a pun with a second meaning, intended to evoke the notion of
a place to lock away your source code securely so it doesn't get out of hand.
