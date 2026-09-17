
## Use of annotation properties for pipeline-specific workflows

OWL annotation properties can be used to attach metadata to classes/relationships without affecting logical reasoning. 

We use custom annotation properties for application-specific behaviour or pipeline-specific workflows.

Some examples:

- [**`labellableRoot`**](https://github.com/BuroHappoldMachineLearning/ADIRO/blob/8b16ca55eacdfa8d991d0f22e14e90d0071dc83f/src/aec_drawing_metadata.ttl#L40): A boolean we use to mark which classes can serve as labels in annotation pipelines. These classes can be surfaced in an annotation software as concepts that can be labelled by human annotators.
- [**`isCVATProperty`**](https://github.com/BuroHappoldMachineLearning/ADIRO/blob/8b16ca55eacdfa8d991d0f22e14e90d0071dc83f/src/aec_drawing_metadata.ttl#L35) used to alter the display of a certain element in the annotation software that we use (CVAT).


Other annotation properties (e.g. `rdfs:label`, `rdfs:comment`) follow standard OWL usage.
