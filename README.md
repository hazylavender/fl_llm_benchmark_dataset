# fl_llm_benchmark_dataset

## Congressional Dataset
This code collects congressional/parliamentary dataset across US, UK and Canada. The dataset is hosted in the hugging face repo https://huggingface.co/datasets/hazylavender/CongressionalDataset 


## Biorxiv 
This code collects biorxiv abstracts under liscence `'cc_by_nc_nd', 'cc_by_nd', 'cc_by_nc', 'cc_by', 'cc0'`. The dataset is hosted in the hugging face repo https://huggingface.co/datasets/hazylavender/biorxiv-abstract

This dataset contains speeches extracted from government institutions of the US, UK and Canada. 
Each speech is a single partition and contains metadata such as speaker name, date, country, and the source URL.

The raw dataset is a list of dictionaries object like below

{
    "url": "https://www.ourcommons.ca/Content/House/441/Debates/335/HAN335-E.XML",
    "date_str": "2024-06-19",
    "title": "Prime Minister's Award for Excellence in Early Childhood Education",
    "speaker": "Mr. Mike Kelloway",
    "data": "it is a privilege to rise in the House today to recognize a constituent of mine who has received the Prime Minister's Award for Teaching Excellence….",
    "chamber": "HOUSE OF COMMONS",
    "country": "CA"
  },


## Using the dataset

To use this dataset, use any libraries of your liking, for example
```
from mlcroissant import Dataset

ds = Dataset(jsonld="https://huggingface.co/api/datasets/hazylavender/CongressionalDataset/croissant")
records = ds.records("default")
```

To filter on dates (or any other fields), you can do
```
import itertools
import pandas as pd

df = (
    pd.DataFrame(list(itertools.filterfalse(lambda x: x['default/date_str'].decode() < '2024-01-01', records)))
)
```


**Data sources and license information**

US
* Source: https://www.congress.gov/congressional-record 
* License: https://www.loc.gov/collections/publications-of-the-law-library-of-congress/about-this-collection/rights-and-access/#:~:text=Publications%20of%20the%20Law%20Library%20of%20Congress%20are%20works%20of,free%20to%20use%20and%20reuse. 
* API: https://api.govinfo.gov/docs/ 

Canada
* Source: https://www.ourcommons.ca/documentviewer/en/44-1/house/sitting-340/hansard 
* License: https://www.ourcommons.ca/en/open-data 
* API: https://api.openparliament.ca
  
UK
* Source: https://hansard.parliament.uk/ 
* License: https://www.parliament.uk/site-information/copyright/ 
* API: https://www.theyworkforyou.com/
  
Biorxiv
* Source: https://www.biorxiv.org/ 
* API: https://api.biorxiv.org/ 
* License information: https://www.biorxiv.org/about/FAQ 
