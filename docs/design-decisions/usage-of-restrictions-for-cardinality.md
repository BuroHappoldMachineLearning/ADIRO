
## Usage of OWL restrictions for cardinality

To express concepts like "Class A can contain Class B" (0 or more) at the class level, we use an **OWL restriction** with qualified cardinality:

```turtle
:Layout rdfs:subClassOf [ rdf:type owl:Restriction ;
                         owl:onProperty :contains ;
                         owl:minQualifiedCardinality 0 ;
                         owl:onClass :Annotation
                       ] .
```

Min cardinality 0 means "can contain" (optional). Use min ≥ 1 for "must contain".

The same form states that a class carries a **datatype property**: the restriction names a data range instead of a class (`owl:onDataRange` in place of `owl:onClass`):

```turtle
:Layout rdfs:subClassOf [ rdf:type owl:Restriction ;
                         owl:onProperty :layoutTitle ;
                         owl:minQualifiedCardinality 0 ;
                         owl:onDataRange xsd:string
                       ] .
```

ADIRO does this for the datatype properties that are computer-vision labels (`isComputerVisionLabel`, see [Use of annotation properties](usage-of-annotation-properties.md)), so that the class that owns a text field names it, and annotation tooling can reach the property from the class. It adds no obligation: min 0 reads "can carry".
