# Student internal documentation

This repository contains both the CSCI E-11 exercises and the source code for
the `e11` system. Students are encouraged to read the implementation and ask
the course staff how it works.

## The course checkout and the `e11` command

The files have two related but separate update mechanisms:

- `$HOME/course` is a Git checkout containing the labs, starter code,
  documentation, graders, and the source for the course services. Updating the
  checkout gives students corrections and improvements to those files.
- The `e11` command is installed as a uv tool in `$HOME/.local/bin`. Released
  versions will be installed from versioned wheels published with GitHub
  releases; the command will not be built or installed from a student's
  checkout.

The course repository specifies the exact released version of `e11` that it
requires. This keeps the installed command, the graders, and the course
services compatible while retaining a single repository in which students can
read all of the source.

## Updating

Students use one command:

```console
$ e11 update
```

The completed updater will automatically:

1. Temporarily save tracked changes in `$HOME/course`.
2. Update the course checkout from GitHub.
3. Restore the tracked changes.
4. Read the required `e11` version from the updated checkout.
5. Download and verify that version's wheel from its GitHub release.
6. Install the wheel with uv and verify the resulting installation.

Untracked files are not included in the temporary save and are not removed by
the updater. If Git cannot combine a course update with a student's tracked
changes, the updater must stop, preserve the saved changes, and explain how to
recover them.

## Why the source remains here

The monorepo lets a single reviewed change update a lab, its grader, the
student command, and the server implementation together. It also lets students
inspect the software that checks their work. The released wheel makes the
installed command reproducible without separating its source from the course.

## Implementation status

This document describes the intended release-wheel update contract. The
current `e11 update` implementation still reinstalls `e11` from the local
checkout and must be replaced before this workflow is presented as complete.
