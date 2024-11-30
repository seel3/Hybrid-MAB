# masterprojekt
github repo for master project

## TODO

* welche richtung soll prototyp verbessert werden?
    * implementierung in keras/tf?
        größter benefit hinsichtlich performance. Kann jedochj sein,dass innerhalb der projektzeit nicht möglich ist. 

    * versuch methoden hinsichtlich detection rate zu verbessern in bestehendem projekt. Performance bleibt schlecht. Kann jedoch detection rate verbessern

    * umstieg auf ganz anderen ansatz z.B. gym malware (Deep Q/Reinforcement learning) oder secml(Genetische Algorythmen)

* Dokumentation der Ansätze genauer? Evaluierung in tabellarischer Form, genauere gegenüberstellung?

### Meeting 29.11.2024

Kolloquium sagen: unterschied zwischen Sandbox ansatz und functionality preserving

warum functionality preservingness besser ist

Für kolloquium alles erklären

gib acht alle Begriffe zu erklären dass sie jeder versteht.

wichtige erkenntnis is dass es aus sicht des eval schritts enorm schwer zu bewerten sind. Grundsatzentscheidung ausschließen wo man test nicht machen kann.

Fokus auf Prototyp und Entscheidung die in dem meeting getroffen wurden.

Erklärung für alle Fachbegriffe

Operation raussuchen und die ersetzten mit Neuronalem netzwerk.
    Thompson sampling z.B. könnt erbessert werden.
    Approximate steps through Neural network

    Nicht neu implemetieren in keras sondern am code arbeiten.


    hyperunsensibles modell das defender ersetzt teils. Modell finetunen oder existierendes nutzen.

    nutzen von confidence level von e.g. malcon um defender aufruf zu ersetzten. z.b. erst ab 50% confidence von malconv den windows defender befragen zu malware sample.

