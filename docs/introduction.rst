Introduction
============

Why
---

Imagine a simple dataset that describes grants. Chances are if is to represent the world, it is going to need to contain some one-to-many relationships (.e.g. one grant, many categories). This is structured data. 

But, consider two audiences for this dataset:

**The developer** wants structured data that she can iterate over, one record for each grant, and then the classifications nested inside that record. 

**The analyst** needs flat data - tables that can be sorted, filtered and explored in a spreadsheet. 

Which format should the data be published in? Flatten Tool thinks it should be both. 

By introducing a couple of simple rules, Flatten Tool is aiming to allow data to be round-tripped between JSON and flat formats, sticking to sensible idioms in both flat-land and a structured world. 

How 
---

Flatten Tool was designed to work along with a JSON Schema. Flatten Tool likes
JSON Schemas which:

**(1) Provide an "id" at every level of the structure**

So that each entity in the data structure can be referenced easily in the flat
version. It turns out this is also pretty useful for JSON-LD mapping.

**(2) Describes the ideal root table by rolling up properties**

Often in a data structure, there are only a few properties that exist at the
root level, with most properties at least one level deep in the structure.
However, if Flatten Tool hides away all the important properties in sub tables,
then the spreadsheet user has to hunt all over the place for the properties
that matter to them.

So, we introduce a custom 'rollUp' property to out JSON Schema. This allows the
schema to specify which relationships and properties should be included in the
first table of a spreadsheet.

You can even roll up fields which *could* be one-to-many, but which often will
be one-to-one relationships, so that there is a good chance of a user of the
flattened data being able to do all the data creation or analysis they want in
a single table.

**(3) Provide unique field titles**

"Recipient Org: Name" is a lot friendlier to spreadsheet users than
'recipientOrganization/name'. So, Flatten Tool includes support for using the
titles of JSON fields instead of the field names when creating a spreadsheet
template and converting data.

But - to make that use, the titles at each level of the structure do need to be
unique.

**(4) Don't nest too deep**

Whilst Flatten Tool can cope with multiple layers of nesting in a data
structure, the deeper the structure gets, the trickier it is for the
spreadsheet user to understand what is going on. So, we try and just go a few
layers deep at most in data for Flatten Tool to work with. 
