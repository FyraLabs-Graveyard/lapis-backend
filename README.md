# Lapis - A build system for the modern age.

Lapis is a artifact build system made (primarily) for Yum/DNF Repositories inspired by [COPR](https://copr.fedorainfracloud.org/) and Pungi. It is to be the official build system for Ultramarine Linux.

It is designed for easy configurability, and ease of contribution.

The Lapis backend is written in Python, and uses PostgreSQL for the database backend.

It uses standard Mock config files to configure the buildroots for each build, and `createrepo` for full repo generation.

## Features
- Yum/DNF repo generation
- Mock config-based buildroots
- (planned) Interoperability with Koji
- (planned) Docker and support for non-RPM distros
