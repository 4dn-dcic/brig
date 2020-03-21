====
brig
====

Conceptually, an offspring of Torb, but following a different path.

Overview
========

This repo provides a place to lock away source code for lambda functions,
so they can be under source control and we can have additional tests and
supporting information that has no place in the AWS lambda function
interface.

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
    |   +-- build-zip  <-- a script that will build any function if invoked from its folder
    |   :                  with the recommended file structure.
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
    |   |   |   |   |                      (loaded automatically by build-zip)
    |   |   |   |   +-- scripts/       <-- utility scripts to help manage function-1
    |   |   |   |   +-- src/           <-- your source code for function-1
    |   |   |   |   +-- tests/         <-- test code for function-1
    |   |   |   |   +-- tmp/           <-- (not for checkin) reserved for building zips of function-1
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
    |   |   |                              (loaded automatically by build-zip)
    |   |   +-- scripts/               <-- utility scripts to help manage function-1
    |   |   +-- src/                   <-- your source code for function-1
    |   |   +-- tests/                 <-- test code for function-1
    |   |   +-- tmp/                   <-- (not for checkin) reserved for building zips of function-1
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
