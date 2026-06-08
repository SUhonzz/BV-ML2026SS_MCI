---
name: AGENTS
description: "Central registry and decision guide for agent customization in this academic writing workspace."
---

# Agent Customization Registry

## Project Overview
This workspace is configured for **Academic Writing Assistance** with heavy orientation toward the `Sources/` folder. All agents and instructions apply the standards from:
- `Academic_walkthrough.pdf` → MCI institutional writing standards
- `formatting_rules.tex` → Technical writing, equation, figure, and methodology conventions

## Active Customizations

### 1. Root-Level Agent Instructions
**File**: `copilot-instructions.md`
- **Scope**: Applies to all interactions in this workspace
- **Purpose**: Establishes academic writing assistant role and PDF extraction protocol
- **Key Feature**: Mandatory pdf-reader skill for all Source PDFs

**Requires**: `pdf-reader` skill from `.agents/skills/pdf-reader/`

### 2. LaTeX Writing Standards
**File**: `.github/instructions/latex-academic-writing.instructions.md`
- **Applies to**: All `.tex` files (`**/*.tex`)
- **Purpose**: Enforces formatting conventions for equations, figures, tables, cross-references
- **Based on**: `formatting_rules.tex` examples and templates

### 3. Academic Writing Principles
**File**: `.github/instructions/academic-writing-principles.instructions.md`
- **Applies to**: Document content and structure across all writing tasks
- **Purpose**: Ensures coherent, rigorous academic writing following MCI standards
- **Based on**: `Academic_walkthrough.pdf` section organization and tone requirements

## Skills Integration

### PDF Reader Skill
**Location**: `.agents/skills/pdf-reader/`

**When Triggered**: Whenever a new PDF appears in `Sources/` or user asks to ingest source material

**Workflow**:
1. Verify PDF exists and is readable
2. Convert using: `python3 ./.agents/skills/pdf-reader/scripts/pdf_to_markdown.py "<input.pdf>" "<output.md>"`
3. Store extracted file as `<original>.extracted.md` next to PDF
4. Read and summarize extracted content
5. Reference specific pages for traceability

**Current Source PDFs to Process**:
- `Sources/Academic_walkthrough.pdf.extracted.md` ✓ (already extracted)
- `Sources/formatting_rules.tex` (LaTeX file, not PDF)
- Any new PDFs added to `Sources/`

## Decision Matrix

| Task | Agent/Instruction | Rationale |
|------|-------------------|-----------|
| Writing new lab report | `academic-writing-principles` + `latex-academic-writing` | Ensures structure and LaTeX compliance |
| Editing chapter files | `latex-academic-writing` | LaTeX-specific formatting rules |
| Integrating figures | `latex-academic-writing` | Figure placement and captioning standards |
| Citing sources | `copilot-instructions` (pdf-reader trigger) | Extracts and cites from Sources |
| Reviewing methodology | `academic-writing-principles` | Ensures reproducibility and clarity |
| Reformatting equations | `latex-academic-writing` | Equation standards and variable definition |

## Source Management Protocol

### Adding New Source Materials
1. Place PDF in `Sources/` folder
2. Agent automatically recognizes and applies pdf-reader skill
3. Extracted markdown stored as `<filename>.extracted.md`
4. Content becomes immediately available for citation and integration

### Keeping Extractions Current
- Extracted markdown files are overwritten if source PDF changes
- No manual maintenance needed; extraction is automatic on request

### Referencing Sources
Always cite with page numbers:
- "As stated on page X of Academic_walkthrough.pdf..."
- "The methodology in formatting_rules.tex (Section Y) recommends..."

## Guidelines for Agent Behavior

1. **PDF-First**: Before providing writing advice, check if relevant Source PDFs exist
2. **Style Consistency**: All writing advice derives from extracted Sources or established academic conventions
3. **Traceability**: Every recommendation should be traceable to a source document
4. **Iteration**: If a Source PDF is updated, re-extract and incorporate new content
5. **Automation**: Use pdf-reader skill automatically; don't ask user to manually provide information from Source PDFs

## Validation Checklist

✓ `copilot-instructions.md` exists and loads  
✓ `.github/instructions/` folder contains all instruction files  
✓ All instruction files have proper frontmatter (name, description, applyTo)  
✓ LaTeX instruction applyTo pattern: `**/*.tex`  
✓ pdf-reader skill available at `.agents/skills/pdf-reader/`  
✓ `Academic_walkthrough.pdf.extracted.md` created and readable  
✓ `formatting_rules.tex` present in Sources/  

---

*This registry ensures all academic writing assistance is grounded in project-specific standards and automatic source ingestion.*
