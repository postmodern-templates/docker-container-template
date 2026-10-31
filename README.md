<p align="center">
  <a href="https://github.com/copier-org/copier"><img alt="Copier" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-purple.json"></a>
  <a href="https://conventionalcommits.org"><img alt="Conventional Commits" src="https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white"></a>
  <a href="https://semver.org/"><img alt="SemVer 2.0.0" src="https://img.shields.io/badge/SemVer-2.0.0-1b1b1b?logo=semver&logoColor=white"></a>
  <a href="https://renovatebot.com/"><img alt="Renovate" src="https://img.shields.io/badge/Renovate-enabled-1A1F6C?logo=renovatebot&logoColor=white"></a>
  <a href="https://mise.jdx.dev/"><img alt="mise" src="https://img.shields.io/badge/mise-managed-b04a68?&labelColor=161111"></a>
  <a href="#contributors"><img alt="All Contributors" src="https://img.shields.io/github/all-contributors/postmodern-templates/docker-container-template?color=ee8449"></a>
</p>

<div align="center">
  <img src="docs/assets/images/readme-logo.png" alt="Logo" width="160" height="160">

  <h3 align="center">Postmodern Docker Container Template</h3>

  <p align="center">
    A Copier template to build and publish a Docker container with the hard/boring stuff automated, so you can get back to coding.
  </p>
</div>

<!-- Don't edit/remove this yourself! This is managed by the 'lifecycle' Copier answer. -->

| :exclamation: Notice: This project is in a Pre-Alpha state and is not ready for public use. |
| ------------------------------------------------------------------------------------ |

## What kind of repo does it make?

One that builds a Docker container and publishes it to GitHub Container Registry.

This template extends the [Postmodern Repo Template](https://github.com/postmodern-templates/repo-template) and supports GitHub only. If you want a repo that releases something other than a container, start there instead.

## What sorts of Hard/Boring stuff does it automate?

- Building amd64 and arm64 Images
- Publishing Images and Build Attestations to GitHub Container Registry
- Matching Container UID and GID to the Host for Bind Mounts
- Versioning and Releasing
- Security and Dependency Updating
- Linting, Styling, and Testing for every Commit and Pull Request
- Publishing Documentation
- License and Policies
- Contribution Guide and Automatic Contributor Crediting

See documentation below for more details on each item.

## Documentation

For detailed documentation, see [https://postmodern-templates.github.io/docker-container-template/](https://postmodern-templates.github.io/docker-container-template/).

## Questions/Comments

Ask a question by opening an issue with the **Question** form.

## Contributing/Bug Reporting

Contributions and bug reports are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).

## Contributors

<!-- spell-checker:disable -->
<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/natescherer"><img src="https://avatars.githubusercontent.com/u/376408?v=4?s=100" width="100px;" alt="Nate Scherer"/><br /><sub><b>Nate Scherer</b></sub></a><br /><a href="#maintenance-natescherer" title="Maintenance">🚧</a> <a href="#code-natescherer" title="Code">💻</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->
<!-- spell-checker:enable -->

This project follows the [all-contributors](https://allcontributors.org) specification.
Contributions of any kind are welcome.

## License

This project is licensed under the MIT License; see [LICENSE](LICENSE).

## Repository Template

This repository is based on the [Postmodern Repo Template](https://github.com/postmodern-templates/repo-template).
