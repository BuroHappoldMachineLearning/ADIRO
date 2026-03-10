# Ontology Modularization Summary

## Overview

The monolithic ontology `aec_drawing_ontology.ttl` has been successfully modularized into five separate ontology files following a strict import hierarchy.

## Module Structure

### 1. Core Ontology (`aec_core.ttl`)
**Namespace**: `https://burohappoldmachinelearning.github.io/ADIRO/aec-core#`

**Contents**:
- Annotation properties: `:exampleImage`, `:labellableRoot`
- Object properties: `:contains`, `:has`

**Imports**: None (foundation layer)

### 2. Drawing Metadata Ontology (`aec_drawing_metadata.ttl`)
**Namespace**: `https://burohappoldmachinelearning.github.io/ADIRO/aec-drawing-metadata#`

**Contents**:
- Sheet/layout/document structure: `:DrawingSheet`, `:Layout`, `:Metadata`
- Metadata elements: `:Titleblock`, `:Legend`, `:RevisionTable`, `:Note`, `:TextualNote`, `:Image`
- Drawing types: `:DrawingType`, `:Plan`, `:Section`, `:Elevation`, `:Detail`, `:Perspective`
- Detail locations: `:DetailLocation`, `:Base`, `:Corner`, `:Head`, `:SlabEdge`, `:Typical`
- Orientation: `:Orientation`, `:Horizontal`, `:Vertical`, `:Portrait`, `:Landscape`, `:DrawingOrientation`
- Data property: `:refersToDrawingId`

**Imports**: Core, Common Symbols

### 3. Common Symbols Ontology (`aec_common_symbols.ttl`)
**Namespace**: `https://burohappoldmachinelearning.github.io/ADIRO/aec-common-symbols#`

**Contents**:
- Generic drawing element: `:DrawingElement`
- Future: dimensions, callouts, grids, levels, etc. (reusable non-domain symbols)

**Imports**: Core, Drawing Metadata

### 4. Domain-common Ontology (`aec_domain_common.ttl`)
**Namespace**: `https://burohappoldmachinelearning.github.io/ADIRO/aec-domain-common#`

**Contents**:
- Property classes: `:MaterialProperties`, `:Material`, `:FunctionalProperties`, `:Function`, `:GeometricProperties`, `:SectionProperties`, `:StructuralProperties`
- Material subclasses: `:Aluminium`, `:Concrete`, `:Glass`, `:Metal`, `:Timber`, `:Polycarbonate`, `:Precast`, `:Clay`
- Facing materials: `:FacingMaterial`, `:Brick`, `:Stone`, `:Terracotta`
- Section/shape properties: `:SectionShape`, `:GenericShapeProperty`, `:Symmetry`, `:CHS`, `:ISection`, `:RHS`, `:SectionChannel`, `:TopHat`, `:Circular`, `:Rectangular`, `:Square`, `:Asymmetrical`, `:Symmetrical`
- Structural properties: `:DeadLoad`, `:Restraint`
- Structural components: `:StructuralComponent`, `:LinearStructuralComponent`, `:PanelStructuralComponent`, `:StructuralMember`, `:Beam`, `:Column`, `:ChordBracing`, `:Cable`, `:Slab`, `:Wall`, `:Upstand`

**Imports**: Core, Drawing Metadata, Common Symbols

### 5. Facade Domain Ontology (`aec_facade_domain.ttl`)
**Namespace**: `https://burohappoldmachinelearning.github.io/ADIRO/aec-facade-domain#`

**Contents**:
- Facade drawing elements: `:FacadeComponent`, `:FacadeSystem`
- Component categories: `:LinearComponent`, `:PanelComponent`, `:PointComponent`
- Facade systems: `:CavityWallSystem`, `:CurtainWallSystem`, `:PrecastSystem`, `:RainscreenSystem`
- All facade-specific subclasses (e.g., `:DGU`, `:TGU`, `:Bracket`, `:BackingWall`, `:RoofCladding`, etc.)
- Facade property classes: `:CWFrameMemberProperties`, `:GlazingProperties`, `:FacadeShape`, `:FrameType`, `:GlazingRetention`, `:CWSystem`
- Facade function subclasses: `:Aesthetic`, `:Airtightness`, `:FireCompartmentation`, `:Thermal`, `:Vision`, `:Waterproofing`

**Imports**: Core, Drawing Metadata, Common Symbols, Domain-common

## Import Hierarchy

```
Core (no imports)
  ↓
Drawing Metadata (imports Core)
  ↓
Common Symbols (imports Core + Drawing Metadata)
  ↓
Domain-common (imports Core + Drawing Metadata + Common Symbols)
  ↓
Facade Domain (imports Core + Drawing Metadata + Common Symbols + Domain-common)
```

## Key Design Decisions

1. **DrawingElement placement**: Placed in Common Symbols as a generic class that any symbols (domain-specific or generic) will subclass.

2. **Structural components**: Placed in Domain-common as they are shared between facade and structural domains.

3. **Property classes**: Generic property classes (Material, Function, etc.) are in Domain-common. Facade-specific property classes (CWFrameMemberProperties, GlazingProperties) are in Facade Domain.

4. **Function subclasses**: Facade-specific function subclasses (Aesthetic, Airtightness, etc.) are in Facade Domain, subclassing the generic `:Function` from Domain-common.

5. **Section/shape properties**: Placed in Domain-common as they are shared between facade and structural domains.

6. **DrawingSheet restrictions**: Removed the domain-specific restriction referencing `:FacadeComponent` to keep Drawing Metadata domain-agnostic.

## Validation

All ontologies have been validated for:
- Correct OWL structure
- No circular references
- Proper import relationships
- Valid namespace usage

## Files Created

- `aec_core.ttl`
- `aec_drawing_metadata.ttl`
- `aec_common_symbols.ttl`
- `aec_domain_common.ttl`
- `aec_facade_domain.ttl`
- `versions/v01/` (directory for version backups)
- `versions/README.md` (versioning documentation)
