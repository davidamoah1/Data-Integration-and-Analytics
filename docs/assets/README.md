# Assets Directory

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Technical Writer

---

## Purpose

Repository for diagrams, images, screenshots, and icons used in documentation.

## Scope

All visual assets referenced by documentation.

## Audience

Documentation contributors.

---

## Directory Structure

```
assets/
├── diagrams/     # Mermaid source files and exported images
├── screenshots/  # Application screenshots
├── icons/        # Custom icons and logos
└── README.md     # This file
```

## Conventions

- **Diagrams**: Mermaid source (`.mmd`) and exported PNG/SVG
- **Screenshots**: PNG format, named by page/feature (e.g., `dashboard-overview.png`)
- **Icons**: SVG format, optimized
- **Naming**: `kebab-case` for all filenames
- **Size**: Optimize images for web (use `pngquant` or `svgo`)

## Usage in Documentation

```markdown
![Dashboard Overview](../assets/screenshots/dashboard-overview.png)
```

## Current Assets

> No assets have been added yet. Screenshots and diagrams will be added in future documentation iterations.

## Related Documents

- [../STYLE_GUIDE.md](../STYLE_GUIDE.md) — Style guide
- [../README.md](../README.md) — Documentation index
