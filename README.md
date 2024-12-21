# masterprojekt
github repo for master project

## TODO

* Add a confidence value for each sample to the sample object
* Add functionality to the samples manager so it can update the confidence value of a sample
* Check for each sample if confidence value is below a certain threshold and query av/model depending on it


### Meeting 29.11.2024

Kolloquium sagen: unterschied zwischen Sandbox ansatz und functionality preserving

warum functionality preservingness besser ist

Für kolloquium alles erklären

gib acht alle Begriffe zu erklären dass sie jeder versteht.

wichtige erkenntnis is dass es aus sicht des eval schritts enorm schwer zu bewerten sind. Grundsatzentscheidung ausschließen wo man test nicht machen kann.

Fokus auf Prototyp und Entscheidung die in dem meeting getroffen wurden.

Erklärung für alle Fachbegriffe





Operation raussuchen und die ersetzten mit Neuronalem netzwerk.
    Thompson sampling z.B. könnte erbessert werden.
    Approximate steps through Neural network

    Nicht neu implemetieren in keras sondern am code arbeiten.


    hypersensibles modell das defender ersetzt teils. Modell finetunen oder existierendes nutzen.

    nutzen von confidence level von e.g. malconv um defender aufruf zu ersetzten. z.b. erst ab 50% confidence von malconv den windows defender befragen zu malware sample.

