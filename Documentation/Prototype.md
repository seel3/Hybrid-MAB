# Prototype

## Basic Concept

## Implementation

## Improvement
A possible Improvement could be to partially substitute defender. Depending on how long it takes to query defender it could be beneficial to only query defender whenever the substitute model confidence crosses a certain threshold. 

For example: 
* Substitue model says sample is 60% malicious or below -> query defender.
* Above 60% defender does not have to be queried
