# **Task Documentation**

# Introduction

This document describes the tasks that are currently implemented or about to be implemented in CommAI-env. The document is used by CommAI-env developers to keep track of task specifications. However, it should also be useful to users/system developers interested in a high-level view of the tasks, their relations and motivation.

**NB1: We did not try to enforce consistency in the specifics of task implementation. For example: in some tasks the Teacher gives more explicit instructions to the learner whereas in others, it doesn't. In some tasks, the Learner must explicitly terminate its message with a period, and in other it doesn't, etc. We consider this sort of noise beneficial, as a smart Learner should be able to cope with high degrees of variability even when encountering similar situations.**

**NB2: Not all tasks described here have already been implemented (those without a [CHK] or a [IMP] tag aren't), and not all tasks that have been implemented are implemented exactly as described here.**



# Repetition Tasks

### **Be Silent [K0][CHK]**

* **Description:** the learner needs to be silent for some time
* **Example 1:**
    * **Teacher:** be silent now.
    * **Learner:**
    * **Teacher:** correct. [R+1]
* **Example 2:**
    * **Teacher:** do not say anything.
    * **Learner:**
    * **Teacher:** correct. [R+1]
* **Motivation:** learn to produce 0 bits (silence) until the teacher is happy.
* **Rewards:** +1 if silent for the entire period
* **Max Time:** chosen randomly between 100 and 1000

### **Do Not Be Silent**

* **Description:** the learner can say anything it wants
* **Example 1:**
    * **Teacher:** do not be silent now.
    * **Learner:** blablabla.
    * **Teacher:** correct. [R+1]
* **Example 2:**
    * **Teacher:** say anything you want.
    * **Learner:** blablabla.
    * **Teacher:** correct. [R+1]
* **Motivation:** learn to produce non-zero bits (noise).
* **Rewards:** +1 if not-silent
* **Max Time:** 100

### **Repeat Character [G15][CHK]**

* **Description:** the learner is asked to repeat the character after the teacher.
* **Example 1:**
    * **Teacher:** say a.
    * **Learner:** a.
    * **Teacher:** correct. [R+1]
* **Example 2:**
    * **Teacher:** repeat a.
    * **Learner:** blablabla.
    * **Teacher:** wrong, correct answer is: a.
* **Max Time:** 1000
* **Motivation:** learners learn the sequences that make valid characters.

### **Do Not Repeat Character**

* **Description:** the learner is asked not to repeat the character after the teacher.
* **Example 1:**
    * **Teacher:**  do not say a.
    * **Learner:**
    * **Teacher:** correct. [R+1]
* **Example 2:**
    * **Teacher:** don’t repeat a.
    * **Learner:** blablabla.
    * **Teacher:** wrong, be silent.
* **Max Time:** 1000
* **Motivation:** learners learn the concept of being silent, negation, simple parsing, and (hopefully) similarity of the words say and repeat.

### **Repeat What I Say [K2][CHK]**

* **Description:** the learner has to repeat the target input that is located on the right side of some frame words.
* **Example 1:**
    * **Teacher:** say apple.
    * **Learner:** apple.
    * **Teacher:** correct. [R+1]
* **Example 2:**
    * **Teacher:** repeat hello world.
    * **Learner:** hello world.
    * **Teacher:** correct. [R+1]
* **Example 3:**
    * **Teacher:** repeat hello world.
    * **Learner:** blabla.
    * **Teacher:** wrong.
* **Max Time:** 1000
* **Motivation:** learners learn the concept of repetition, simple parsing, and (hopefully) similarity of the words say and repeat.
* **Prerequisites:**

### **Repeat What I Say 2 [K3][CHK]**

* **Description:** the learner has to repeat the target input after the teacher. The target input is located in the middle of some frame words.
* **Example 1:**
    * **Teacher:** say apple and you will get a reward.
    * **Learner:** apple.
    * **Teacher:** correct. [R+1]
* **Example 2:**
    * **Teacher:** repeat hello world to get a reward.
    * **Learner:** blablabla.
    * **Teacher:** wrong.
* **Max Time:** 1000
* **Timeout Message**: wrong, incorrect, etc.
* **Motivation:** learners learn the concept of repetition, parsing, and (hopefully) similarity of the words say and repeat.
* **Prerequisites:** [K2]

### **Repeat What I Say Multiple Times [K5][CHK]**

* **Description:** the learner has to repeat the word after the teacher multiple times.
* **Example 1:**
    * **Teacher:** say apple 3 times.
    * **Learner:** apple apple apple.
    * **Teacher:** correct. [R+1]
* **Example 2:**
    * **Teacher:** repeat apple 2 times.
    * **Learner:** blablabla.
    * **Teacher:** wrong, correct answer is: apple apple.
* **Max Time:** 10000
* **Timeout Message**: wrong, correct answer is: [target] [target] (repeated N times).
* **Motivation:** learners learn to repeat a word or phrase multiple times (a simple form of counting).

### **Repeat What I Say Multiple Times 2 [K6][CHK]**

* **Description:** the learner has to repeat the words after the teacher multiple times.
* **Example 1:**
    * **Teacher:** say apple 3 times and you will get a reward.
    * **Learner:** apple apple apple.
    * **Teacher:** correct. [R+1]

* **Example 2:**
    * **Teacher:** repeat apple 2 times and you will pass this task.
    * **Learner:** blablabla.
    * **Teacher:** wrong, correct answer is: apple apple.
* **Max Time:** 10000
* **Timeout Message**: wrong, correct answer is: [target] [target] (repeated N times).
* **Motivation:** learners learn to repeat a word or a phrase multiple times.

### **Repeat What I Say Multiple Times Separated By Comma [K7][CHK]**
* **Description:** the learner has to repeat the word after the teacher multiple times. The words should be separated by commas.
* **Example 1:**
    * **Teacher:** say apple 3 times separated by comma.
    * **Learner:** apple, apple, apple.
    * **Teacher:** correct. [R+1]
* **Example 2:**
    * **Teacher:** repeat apple 2 times separated by comma.
    * **Learner:** blablabla.
    * **Teacher:** no, correct answer is: apple, apple.
* **Max Time:** 10000
* **Motivation:** learners learn to repeat a symbol or a word multiple times.

### **Repeat What I Say Multiple Times Separated By And [K8][CHK]**

* **Description:** similar to above. The words should be separated by *and*.
* **Example 1:**
    * **Teacher:** say apple 3 times separated by and.
    * **Learner:** apple and apple and apple.
    * **Teacher:** correct. [R+1]
* **Example 2:**
    * **Teacher:** repeat apple 2 times separated by and
    * **Learner:** blablabla.
    * **Teacher:** no, correct answer is: apple and apple.
* **Max Time:** 10000
* **Motivation:** learners learn to repeat a symbol or a word multiple times.

### **Repeat What I Say Multiple Times Separated By Comma And And [K9][CHK]**

* **Description:** similar to above. The words should be separated by comma first, and then by *and*.
* **Example 1:**
    * **Teacher:** say apple 3 times separated by comma and and.
    * **Learner:** apple, apple and apple.
    * **Teacher:** correct. [R+1]
* **Example 2:**
    * **Teacher:** repeat apple 2 times separated by comma and and.
    * **Learner:** blablabla.
    * **Teacher:** no, correct answer is: apple and apple.
* **Max Time:** 10000
* **Motivation:** learners learn to repeat a symbol or a word multiple times.

### **Repeat What I Say Using Conjunction And Negation [A1][IMP]:**

* **Description:** Learner is asked to repeat after the teacher, but this time using *and* and negation (*don’t, do not*).
* **Example 1:**
    * **Teacher:** say apple and banana.
    * **Learner:** apple and banana.
    * **Teacher:** correct. [R+1]
* **Example 2:**
    * **Teacher:** say apple and don't say banana.
    * **Learner:** apple.
    * **Teacher:** correct. [R+1]
* **Example 3:**
    * **Teacher:** say apple and do not say banana.
    * **Learner:** apple and banana.
    * **Teacher:** wrong, correct answer is: apple. [R+1]
* **Example 4:**
    * **Teacher:** do not say apple and do not say banana.
    * **Learner:**
    * **Teacher:** correct. [R+1]
* **Motivation:** Teach the learner basic logic operations
* **MaxTime**: 1000

### **Repeat What I Say Using Disjunction [A2][IMP]:**

* **Description:** Learner is asked to repeat after the learner, but this time using *or*.
* **Example 1:**
    * **Teacher:** say apple or banana.
    * **Learner:** apple. (or alternatively banana)
    * **Teacher:** correct. [R+1]
* **Example 2:**
    * **Teacher:** say apple or banana.
    * **Learner:** apple or banana.
    * **Teacher:** wrong.
* **Motivation:** Teach the learner basic logic operations
* **MaxTime**: 1000

### **Verbs [G0][IMP]:**

* **Description:** Learner is asked to do something.
* **Instructions:** Say 'I V' to V.
* **Example:**
    * **Teacher:** Say 'I sing' to sing.
    * **Learner:** I sing.
    * **Teacher:** You sang [+1].
* **Motivation:** Teach the learner how to perform actions (even if they have no effect for now).
* **Rewards:** +1 for correct answer
* **MaxTime**: Len(Instructions) + Len(I sing)
* **Timeout Message**: Generic "time is out" message.
* **Prerequisites:** repeating strings in context

* **Teacher inputs:** Say 'I V' to V. where V is in a list of verbs defined in german_tasks


## Counting

### **Counting [T1][IMP]:**
* **Description:** the learner should know how many objects the teacher has based on communication only.
* **Instruction:** Count the objects.
* **Example 1:**
    * **Teacher:** I have an apple, an apple and a banana. How many bananas do I have?
    * **Learner:** one
* **Motivation:** To learn basic counting.
* **Prerequisites:** T2, T3
* **Teacher inputs:** generated from a simple grammar



## **Objects & Properties**

### **Object existence 1 [T2][IMP]:**

* **Description:** the learner needs to understand which objects are present, and teacher should guide it through communication when learner is wrong
* **Instruction:** Let's play a game with fruits.
* **Example 1:**
    * **Teacher:** I have an apple. Do I have a banana?
    * **Learner:** yes
    * **Teacher:** wrong, I do not have a banana.
* **Example 2:**
    * **Teacher:** I have an apple. Do I have a banana?
    * **Learner:** no
    * **Teacher:** correct [R+1]
* **Motivation:** To learn about presence of objects.
* **Max_time:** 3000
* **Prerequisites:** -
* **Teacher inputs:** generated from a simple grammar

### **Object existence 2 [T3][IMP]**

* **Description:** the learner needs to understand which objects are present, and teacher should guide it through communication when learner is wrong; increased complexity by having more objects present
* **Instruction: -**
* **Example 1:**
    * **Teacher:** I have an apple and a banana and no pear. Do I have a pear?
    * **Learner:** no
    * **Teacher:** correct [R+1]
* **Motivation:** To learn about presence of objects.
* **Prerequisites:** T2
* **Teacher inputs:** generated from a simple grammar

### **Associate object with property [M1][CHK]**

* **Description:** Learner is presented with an object and an associated property from one of two "baskets" (John's and Mary's), and it must produce the property (followed by period)
* **Instructions:** O in B's basket is P. how is O?
* **Example:**
    * **Teacher:** apple in john's basket is green. how is apple?
    * **Learner:** green.
* **Motivation:** Teaching the learner a set of associations (baskets x objects x properties) to memorize in order to use them in later tasks
* **Rewards:** +1 for correct answer with message randomly selected from list congratulations_messages specified in marco_tasks.py
* **Max Time:** 3000
* **Timeout Message:** the right answer is P.
* **Prerequisites:** ability to identify and repeat a substring
* **Teacher inputs:** O in B's basket is P. how is O? [where B, O and P are baskets, objects and properties, respectively, from the global_properties dict in marco_tasks.py]

### **Verify that object has property [M2][CHK]**

* **Description:** Learner is asked if an object has an associated property in John or Mary's basket, the learner must answer "yes" if the relevant object in the relevant basket has the property. The baskets are the same used in M1.
* **Instructions:** is O P in B's basket?
* **Example 1:**
    * **Teacher:** is apple green in mary's basket?
    * **Learner:** yes.
* **Example 2:**
    * **Teacher:** is apple sweet in john's basket?
    * **Learner:** no. [NB: according to table from M1, apple is sour in John's basket]
* **Motivation:** Testing that learner is able to keep associations in its memory.
* **Rewards:** +1 for correct answer with message randomly selected from list congratulations_messages specified in marco_tasks.py
* **Max Time:** 3000
* **Timeout Message:** the right answer is (yes|no).
* **Prerequisites:** M1, T2 for the ability to answer yes/no questions
* **Teacher inputs:** is O P in B's basket? [where B, O and P are baskets, objects and properties, respectively, from the global_properties dict in marco_tasks.py]

### **List properties of an object [M5][CHK]**

* **Description:** Learner is asked to list the properties of an object from a certain basket, based on the same dictionary used for task M1
* **Instructions:** which properties does O have in B's basket?
* **Example 1:**
    * **Teacher:** which properties does apple have in john's basket?
    * **Learner:** sour hard green. [objects could be listed in any order, and " and “, “, and “ and “, " are other acceptable delimiters, see next example]
* **Example 2:**
    * **Teacher:** which properties does apple have in mary's basket?
    * **Learner:** red, sweet and hard.
* **Motivation:** The learner must keep the table of association from task M1 in memory, and unlike in M2, it must actually explicitly retrieve all of them, rather than verifying one of them, explicitly presented. The system must also perform some parsing to format the output list.
* **Rewards:** +1 for correct answer with message randomly selected from list congratulations_messages specified in marco_tasks.py
* **Max Time:** 3500
* **Timeout Message:** the right answer is P1 .. PN. [listing all Ps of target object in B's basket]
* **Prerequisites:** at the very least M1; K7 and related formatting tasks also seem important
* **Teacher inputs:** which properties does O have in B's basket? [where B and O are baskets and objects, respectively, from the global_properties dict in marco_tasks.py]

### **Name a property of an object [M7][CHK]**

* **Description:** Learner is asked to name one of the properties of an object from a certain basket, based on the same dictionary used for task M1
* **Instructions:** can you tell me a property of O from B's basket?
* **Example 1:**
    * **Teacher:** can you tell me a property of apple in john's basket?
    * **Learner:** sour.
* **Motivation:** The learner must keep the table of association from task M1 in memory. Unlike in M2, it must actually explicitly retrieve one property, rather than verifying it. However, unlike in M5, it suffices for the learner to produce a single property. Note that if the agent produced all properties of an object (green sour and hard.), it would still get reward, but more slowly than if it produced one property only. Thus, to solve this task efficiently the learner must understand the quantification in the teacher's question (one vs all).
* **Rewards:** +1 for correct answer with message randomly selected from list congratulations_messages specified in marco_tasks.py
* **Max Time:** 3000
* **Timeout Message:** one right answer is P. [with P randomly sampled from the objects having the target property in B's basket]
* **Prerequisites:** at the very least M1; M2 and M5 should also help.
* **Teacher inputs:** can you tell me a property of O in B's basket? [where B and O are baskets and objects, respectively, from the global_properties dict in marco_tasks.py]

### **List objects with a certain property [M3][CHK]**

* **Description:** Learner is asked to list the objects that have a certain property in a certain basket, based on the same dictionary used for task M1
* **Instructions:** which objects are P in B's basket?
* **Example 1:**
    * **Teacher:** which objects are yellow in john's basket?
    * **Learner:** pineapple banana. [objects could be listed in any order, and " and “, “, and “ and “, " are other acceptable delimiters, see next example]
* **Example 2:**
    * **Teacher:** which objects are tasteless in mary's basket?
    * **Learner:** banana and pear.
* **Motivation:** The learner must keep the table of association from task M1 in memory. While the task can be solved in various ways, it requires a different offline or online organization of the data with respect to M2 and M5, as the learner must access the associations by value. Succeeding at both M2/M5 and M3 requires some form of algorithmic thinking in terms of structuring the same data in different ways.
* **Rewards:** +1 for correct answer with message randomly selected from list congratulations_messages specified in marco_tasks.py
* **Max Time:** 3500
* **Timeout Message:** the right answer is O1 .. ON. [listing all Os with property P in B's basket]
* **Prerequisites:** at the very least M1; solving M5 should make this easier (and vice versa).
* **Teacher inputs:** which objects are P in B's basket? [where B and P are baskets and properties, respectively, from the global_properties dict in marco_tasks.py]

### **Name an object with a property [M8][CHK]**

* **Description:** Learner is asked to name one of the objects that have a certain property in a certain basket, based on the same dictionary used for task M1
* **Instructions:** can you tell me an object that is P in B's basket?
* **Example 1:**
    * **Teacher:** can you tell me an object that is sour in john's basket?
    * **Learner:** apple.
* **Motivation:** The learner must keep the table of association from task M1 in memory. Unlike in M2, M5 and related tasks, query here is by value (property), not key, requiring a different organization of the data. Moreover, unlike in M3, the learner can produce only one object. Thus, to solve the task efficiently, the learner must understand the quantification in the teacher's question (one vs all).
* **Rewards:** +1 for correct answer with message randomly selected from list congratulations_messages specified in marco_tasks.py
* **Max Time:** 3000
* **Timeout Message:** one right answer is O. [with O randomly sampled from the objects having the target property in B's basket]
* **Prerequisites:** at the very least M1; M2 and M3 should also help. Solving M7 should make this task easier, and vice versa.
* **Teacher inputs:** can you tell me an object that is P in B's basket? [where B and P are baskets and properties, respectively, from the global_properties dict in marco_tasks.py]

### **Who has a certain object with a certain property [M9][CHK]**

* **Description:** Learner is asked about an object with a property (e.g., a green apple), and it has to list all the baskets that have the object (baskets and their objects+properties are as in M1, although the teacher can ask for an object+property combination that never occurs in the baskets).
* **Instructions:** who has a P O in the basket?
* **Example 1:**
    * **Teacher:** who has a yellow pineapple in the basket?
    * **Learner:** john and mary. [also acceptable: (john, mary.| john mary.| john, and mary.) as well as all these forms with the basket names in opposite order]
* **Example 2:**
    * **Teacher:** who has a green apple in the basket?
    * **Learner:** john.
* **Example 3:**
    * **Teacher:** who has an expensive onion in the basket?
    * **Learner:** nobody. [while both property expensive and object onion are in the table, no basket contains an expensive onion]
* **Motivation:** This task requires the learner to perform some relatively sophisticated linguistic and set-based reasoning over the table of associations it had to memorize in M1. First, from a linguistic point of view, the learner has to derive the adjective-noun construction ("green apple") from data that until now have been presented in predicative format (“apple is green”). From the point of view of set-based reasoning, in this task the learner is asked to reason across the baskets, whereas until now it was always told the basket it had to look at . Moreover, the learner must understand the notion of an empty set, if no basket contains objects with the requested properties. Finally, the task requires some non-trivial formatting abilities.
* **Rewards:** +1 for correct answer with message randomly selected from list congratulations_messages specified in marco_tasks.py
* **Max Time:** 3500
* **Timeout Message:**
    * if the object+property combination is present in a basket: the right answer is B1 .. BN. [listing all Bs with the relevant object+property combination]
    * else: the right answer is: nobody.
* **Prerequisites:** at the very least M1; other association tasks might also help, both because they will also require the learner to memorize the same association table, and because they should improve its querying skills; other tasks that might help include K7, T3 and T5. Also, any task involving logical reasoning might help.
* **Teacher inputs:** who has (a|an) P O in the basket? [where P and O are properties and objects, respectively, from the global_properties dict of marco_tasks.py; note that the indefinite article is a unless P begin with vowel]

### **List the properties that an object has in a basket only [M11][CHK]**

* **Description:** Learner is asked about the properties that an object has in only one basket. The learner must thus retrieve the properties of the relevant object from all baskets, and compare them.
* **Instructions:** which properties does O have in B’s basket only?
* **Example 1:**
    * **Teacher:** which properties does apple have in john’s basket only?
    * **Learner:** green, sour, cheap, healthy and local. [other acceptable connectives: ‘ ‘, ‘, and’; any order of properties is acceptable]
* **Example 2:**
    * **Teacher:** which properties does tomato have in mary’s basket only?
    * **Learner:** none. [This is a case--the only one given the state of the baskets as of July 13th 2016-- in which the properties of an object in a basket are a subset of the properties in the other. For the time being, the task is implemented so that it won’t generate "trick" questions concerning objects that are ONLY in the basket being asked about or NOT in the basked being asked about: I’d say that “only” presupposes that O is present in all baskets, so “which properties does asparagus have in mary’s basket only” is a weird question to ask if mary’s is the only basked with asparagus]
* **Motivation:** This task requires the learner to reason about shared properties across baskets, and more precisely to find *distinctive* properties of an object. This is an important ability to be able to unambiguously refer to things (if both baskets have a hard apple, but only John’s one is green, it’s better to refer to the latter as "the green apple", rather than “the hard apple”).
* **Rewards:** +1 for correct answer with message randomly selected from list congratulations_messages specified in marco_tasks.py
* **Max Time:** 3500
* **Timeout Message:**
    * if O has at least one distinctive property in B: the right properties are P1 .. PN. [listing all distinctive Ps]
    * else: the right properties are: none.
* **Prerequisites:** at the very least M1; other basket reasoning tasks might also help, both because they will also require the learner to memorize the same association table, and because they should improve its analysis skills; also, there should be a beneficial interaction with A1 and other logical tasks.
* **Teacher inputs:** which properties does O have in B’s basket only? [where O and P are properties and baskets, respectively, from the global_properties dict of marco_tasks.py]

### **List the properties that an object has in all baskets [M12][CHK]**

* **Description:** Learner is asked about the properties that an object has in all baskets. The learner must thus retrieve the properties of the relevant object from all baskets, and compare them.
* **Instructions:** which properties does O have in all baskets?
* **Example 1:**
    * **Teacher:** which properties does apple have in all baskets?
    * **Learner:** green, sour, cheap, healthy and local. [other acceptable connectives: ‘ ‘, ‘, and ‘]
* **Example 2:**
    * **Teacher:** which properties does mango have in all baskets?
    * **Learner:** none.
* **NB:** The question will only be asked for objects that are present in ALL baskets, to avoid tricky cases (does an object have a property in all baskets if the object has the property in the only basket in which it occurs?)
* **Motivation:** This task requires the learner to reason about shared properties across baskets, and it’s closely related to M11
* **Rewards:** +1 for correct answer with message randomly selected from list congratulations_messages specified in marco_tasks.py
* **Max Time:** 3500
* **Timeout Message:**
    * If there are properties that target object has in all baskets: the right properties are: P1 .. PN. [listing all Ps that the object has in all baskets]
    * else: the right properties are: none.
* **Prerequisites:** at the very least M1; other basket reasoning tasks might also help, both because they will also require the learner to memorize the same association table, and because they should improve its analysis skills; also, there should be a beneficial interaction with A1 and other logical tasks. Finally, this task and M11 are closely related, and they might be solved jointly.
* **Teacher inputs:** which properties does O have in all baskets? [where O is an object from the global_properties dict of marco_tasks.py]

## Counting + Objects & Properties

### **How many objects have a certain property [M4][IMP]**

* **Description:** Learner is asked to tell how many objects have a property in a certain basket, based on the same dictionary used for task M1
* **Instructions:** how many objects are P in B's basket?
* **Example 1:**
    * **Teacher:** how many objects are yellow in john's basket?
    * **Learner:** two. [banana and pineapple]
* **Example 2:**
    * **Teacher:** how many objects are yellow in john's basket?
    * **Learner:** 2. [NB: both letter transcriptions of numbers up to 10 and digits (any quantity) accepted]
* **Example 3:**
    * **Teacher:** how many objects are blue in mary's basket?
    * **Learner:** zero. [0 would also be acceptable; this should be produced for all properties that are not associated to objects in a basket, where these properties are (random) character strings that are not in the M1 dictionary]
* **Motivation:** The learner must keep the table of association from task M1 in memory, issue queries by property like in M3 and perform numerical reasoning like in M6 and T5. Thus, optimal ways to solve the task would involve putting together queries on a memorized table and the ability to count. Moreover, unlike in the M6 object counting task, the learner must reason about new strings ("properties" that no object in the baskets has)
* **Rewards:** +1 for correct answer with message randomly selected from list congratulations_messages specified in marco_tasks.py
* **Max Time:** 3000
* **Timeout Message:** the right answer is N. [where N is in digits for quantities>10, randomly printed either in letters or digits otherwise]
* **Prerequisites:** at the very least M1; M3 and, especially, M6 and T4/T5 should make this task easier (the numbered repetition tasks K5-K7 should also help).
* **Teacher inputs:** how many objects are P in B's basket? [where B is one of the baskets in the global_properties dict of marco_tasks.py, and P is either a property appearing in the B basket or a random character string]

### **How many properties does an object have [M6][IMP]**

* **Description:** Learner is asked to tell how many properties an object from a certain basket has, based on the same dictionary used for task M1
* **Instructions:** how many properties does O have in B's basket?
* **Example 1:**
    * **Teacher:** how many properties does pineapple have mary's basket?
    * **Learner:** three.
* **Example 2:**
    * **Teacher:** how many properties does banana have in john's basket?
    * **Learner:** 4. [NB: both letter transcriptions of numbers up to 10 and digits (any quantity) accepted]
* **Motivation:** The learner must keep the table of association from task M1 in memory, issue queries by object like in M5 and perform numerical reasoning like in T4/T5, as well as K5-K7. Thus, optimal ways to solve the task would involve putting together queries on a memorized table and the ability to count.
* **Rewards:** +1 for correct answer with message randomly selected from list congratulations_messages specified in marco_tasks.py
* **Max Time:** 3000
* **Timeout Message:** the right answer is N. [where N is in digits for quantities>10, randomly formatted either in letters or digits otherwise]
* **Prerequisites:** at the very least M1; M2/M5 and, especially, T4/T5 (and the simpler K’s counting-repetitions tasks they might depend upon) should make this task easier
* **Teacher inputs:** how many properties does O have in B's basket? [where B and O are, respectively, a basket and an object in the global_properties dict of marco_tasks.py]

### **Italian how many properties does an object have [M10][IMP]**

* **Description:** Same as m6, but in Italian
* **Instructions:** quante proprieta’ ha O nel cestino di B?
* **Example 1:**
    * **Teacher:** quante proprieta’ ha ananas nel cestino di mary?
    * **Learner:** tre.
* **Example 2:**
    * **Teacher:** quante proprieta’ ha banana nel cestino di john?
    * **Learner:** 4. [NB: both letter transcriptions of numbers up to 10 and digits (any quantity) accepted]
* **Motivation:** To illustrate how tasks might be more challenging in a language we’re not familiar with, and the sort of changes (switching language) that systems might encounter from the training to the test environment.
* **Rewards:** +1 for correct answer with message randomly selected from list italian_congratulations_messages specified in the relevant task class in marco_tasks.py
* **NB:** I was not able to unicode-ify (or latin1-ify) the messages, so I am using apostrophes in place of accents
* **Max Time:** 3000
* **Timeout Message:** la risposta corretta e’ N. [where N is in digits for quantities>10, randomly formatted either in letters or digits otherwise]
* **Prerequisites:** solving m6 should make this easier
* **Teacher inputs:** quante proprieta’ ha O nel cestino di B? [where B is a basket and a O the Italian translation of an object from the global_properties dict of marco_tasks.py]

## Question Asking

### **Guess The Number Asking Questions (Explicit Model) [M13][IMP]**
* **Description:** The Learner is told to guess an N-digit number (N from 1 to 5), and shown explicitly how to ask for it. It gets reward when it guesses the number, but it can considerably increase the chances of getting reward if it directly asks the Teacher for the number.
* **Instructions:** guess the N-digit number I am thinking of; you can ask me: please tell me the number.
* **Example 1:**
    * **Teacher:** guess the 3-digit number I am thinking of; you can ask me: please tell me the number.
    * **Learner:** 435.
    * … (time runs out)
    * **Teacher:** if you asked: please tell me the number., I would have said: 554.
* **Example 2:**
    * **Teacher:** guess the 4-digit number I am thinking of; you can ask me: please tell me the number.
    * **Learner:** please tell me the number.
    * **Teacher**: 3211.
    * **Learner:** 3211.
    * **Teacher:** Good job! [R +1]
* **Example 2:**
    * **Teacher:** guess the 4-digit number I am thinking of; you can ask me: what’s the number?
    * **Learner:** please tell me the number. [NB: Learner can use another form for the question]
    * **Teacher**: 1199.
    * **Learner:** 1199.
    * **Teacher:** Bravo! [R +1]
* **Motivation:** This task should teach the Learner how to request information (and use it), to get reward
* **Rewards:** +1 for correct answer with message randomly selected from list congratulations_messages specified in marco_tasks.py
* **Max Time:** 3000
* **Timeout Message:**
    * if you asked: [question model], I would have said: [target number].
* **Prerequisites:** The repetition tasks, any counting task might also help.
* **Teacher inputs:**
    * At beginning: guess the D-digit number I am thinking of; you can ask me: [question model].
    * In response to request for number: [target number].
* **Accepted variations of request (question model):** please tell me the number., what’s the number?, what is the number?, can you tell me the number?

### **Guess The Number Asking Questions [M14][IMP]**

* **Description:** The Learner is told to guess an N-digit number (N from 1 to 5), and told it can ask about it. It gets reward when it guesses the number, but it can considerably increase the chances of getting reward if it directly asks the Teacher for the number.
* **Instructions:** guess the N-digit number I am thinking of; you can ask me for the number.
* **Example 1:**
    * **Teacher:** guess the 3-digit number I am thinking of; you can ask me for the number.
    * **Learner:** 435.
    * … (time runs out)
    * **Teacher:** if you asked: can you tell me the number?, I would have said: 554.
* **Example 2:**
    * **Teacher:** guess the 4-digit number I am thinking of; you can ask me for the number.
    * **Learner:** please tell me the number.
    * **Teacher**: 3211.
    * **Learner:** 3211.
    * **Teacher:** Good job! [R +1]
* **Motivation:** This task should teach the Learner how to request information (and use it), to get reward: if goes beyond M13 in that the Teacher does not provide an explicit model for how to ask the question
* **Rewards:** +1 for correct answer with message randomly selected from list congratulations_messages specified in marco_tasks.py
* **Max Time:** 3000
* **Timeout Message:**
    * if you asked: [question model], I would have said: [target number].
* **Prerequisites:** Clearly, this should benefit from the more explicit M13 (and any other tasks the latter depends upon). Ability to memorize information across tasks (as developed, e.g., in the association tasks) should also help, because the Learner should remember and be able to use the questions that were taught in M13
* **Teacher inputs:**
    * At beginning: guess the D-digit number I am thinking of; you can ask me for the number.
    * In response to request for number: [target number].
* **Accepted variations of request:** same as in M13

### **Guess The Number Asking For Digits (Explicit Model) [M15][IMP]**

* **Description:** The Learner is told to guess an N-digit number (N from 1 to 5), and shown explicitly how to ask for a digit at the time. It gets reward when it guesses the number, but it can considerably increase the chances of getting reward if it directly asks the Teacher for the digits.
* **Instructions:** guess the N-digit number I am thinking of; you can ask me: please tell me the next digit.
* **Example 1:**
    * **Teacher:** guess the 3-digit number I am thinking of; you can ask me: please tell me the next digit.
    * **Learner:** 435.
    * … (time runs out)
    * **Teacher:** if you asked: please tell me the next digit., I would have said: 4; the number is 435.
* **Example 2:**
    * **Teacher:** guess the 4-digit number I am thinking of; you can ask me: please tell me the next digit.
    * **Learner:** please tell me the next digit.
    * **Teacher**: 3.
    * **Learner:** 3.
    * … (time runs out)
    * **Teacher:** if you asked me: what’s the next digit?, I would have said: 1; the number is 3122.
* **Example 2:**
    * **Teacher:** guess the 4-digit number I am thinking of; you can ask me: what’s the next digit?
    * **Learner:** please tell me the next digit. [NB: Learner can use another form for the question]
    * **Teacher**: 1.
    * **Learner:** please tell me the next digit.
    * **Teacher**: 1.
    * **Learner**: what’s the next digit?
    * **Teacher**: 9.
    * **Learner**: can you tell me the next digit?
    * **Teacher**: 9.
    * **Learner**: can you tell me the next digit.
    * **Teacher**: the number has only 4 digits.
    * **Learner:** 1199.
    * **Teacher:** bravo! [R +1]
* **Motivation:** This task should teach the Learner how to request information (and use it), to get reward. Moreover, the Learner must ask for information multiple times, and store and organize the information it receives. Moreover, once it has all the information (it asked all for all digits), the Learner should stop and reply, rather than wasting time asking for more digits.
* **Rewards:** +1 for correct answer with message randomly selected from list congratulations_messages specified in marco_tasks.py
* **Max Time:** 3500
* **Timeout Message:**
    * If there is still a digit that the Learner has not asked for:
        * if you asked: [question model], I would have said: [next digit]. the number is [target number].
    * Else:
        * the number is [target number].
* **Prerequisites:** The repetition tasks, any counting task might also help, the association tasks because of the memory demands.
* **Teacher inputs:**
    * At beginning: guess the D-digit number I am thinking of; you can ask me: [question model].
    * In response to request for digit:
        * If there is still a digit that hasn’t been requested: [next digit].
        * Otherwise: The number has only D digits.
* **Accepted variations of request (question model):** please tell me the next digit., what’s the next digit?, what is the next digit?, can you tell me the next digit?

### **Guess The Number Asking For Digits [M16][IMP]**

* **Description:** The Learner is told to guess an N-digit number (N from 1 to 5), and told it can ask for the next digit. It gets reward when it guesses the number, but it can considerably increase the chances of getting reward if it directly asks the Teacher for the digits.
* **Instructions:** guess the N-digit number I am thinking of; you can ask me for next digit.
* **Example 1:**
    * **Teacher:** guess the 3-digit number I am thinking of; you can ask me for the next digit.
    * **Learner:** 435.
    * … (time runs out)
    * **Teacher:** if you asked: please tell me the next digit., I would have said: 4; the number is 435.
* **Example 2:**
    * **Teacher:** guess the 4-digit number I am thinking of; you can ask me for the next digit.
    * **Learner:** please tell me the next digit.
    * **Teacher**: 1.
    * … (Learner asks for all digits)
    * **Learner:** 1199.
    * **Teacher:** bravo! [R +1]
* **Motivation:** This task should teach the Learner how to request information (and use it), to get reward. Moreover, the Learner must ask for information multiple times, and organize the information it receives. Moreover, once it has all the information (it asked all for all digits), the Learner should stop and reply, rather than wasting time asking for more digits. The task builds on M15, but the Teacher is no longer providing an explicit for how to ask questions
* **Rewards:** +1 for correct answer with message randomly selected from list congratulations_messages specified in marco_tasks.py
* **Max Time:** 3500
* **Timeout Message:**
    * If there is still a digit that the Learner has not asked for:
        * if you asked: [question model], I would have said: [next digit]. the number is [target number].
    * Else:
        * the number is [target number].
* **Prerequisites:** M15, and its dependencies
* **Teacher inputs:**
    * At beginning: guess the D-digit number I am thinking of; you can ask me for the next digit.
    * In response to request for digit:
        * If there is still a digit that hasn’t been requested: [next digit].
        * Otherwise: The number has only D digits.
* **Accepted variations of request (question model):** same as in M15

## **Navigation & Proprioception**

### **Look [AJ1][IMP]**

* **Description:** the learner must look where the teacher tells it to.
* **Instruction:** look where I say
* **Example 1:**
    * **Teacher:** Look to the east
    * **Learner:** I look to the east
* **Rewards:** +1 for correct answer
* **Max Time:** 2 * MAX_INPUT_LENGTH
* **Motivation:** learners learn to look around, gather information about its information.
* **Prerequisites:**
* **Teacher inputs:** look to the east, look to the west, look to the north, look to the south

### **Look Around [AJ2][IMP]**

* **Description:** the learner must look around itself
* **Instruction:** look around
* **Example 1:**
    * **Teacher:** Look around
    * **Learner:** I look to the east
    * **Learner**: I look to the west
    * **Learner**: I look to the north
    * **Learner**: I look to the south
    * **Teacher**: Congratulations!
* **Rewards:** +1 for correct answer
* **Max Time:** 2 * MAX_INPUT_LENGTH
* **Motivation:** learners learn to look around.
* **Prerequisites:**
* **Teacher inputs:**

### **Look For [AJ3][IMP]**

* **Description:** the learner must find an object
* **Instruction:** find the object I want
* **Example 1:**
    * **Teacher:** Look for the banana
    * **Learner:** I look to the east
    * **Teacher**: Congratulations!
* **Rewards:** +1 for correct answer
* **Max Time:** 2 * MAX_INPUT_LENGTH
* **Motivation:** learners learn to look around.
* **Prerequisites:**
* **Teacher inputs:** Look for the banana, Look for the apple, Look for the pineapple, Look for the cherry

### **Turning [G1][IMP]**

* **Description:** Learner is asked to turn in some direction.
* **Instructions:** You will have to turn.
* **Example:**
    * **Teacher:** Turn left/right.
    * **Learner:** I turn left/right
    * **Teacher:** You turned [+1].
* **Motivation:** Teach the learner to turn in whatever sense.
* **Rewards:** +1 for correct answer
* **MaxTime**: Len(Instructions) + 3 TIME_TURN
* **Prerequisites:** repeating strings in context, G0
* **Teacher inputs:** Turn left, Turn right.

### **Moving Forward [G2][IMP]**

* **Description:** Learner is asked to move forward.
* **Instructions:** You will have to move forward.
* **Example:**
    * **Teacher:** Move forward.
    * **Learner:** I move forward.
    * **Teacher:** You moved [+1].
* **Motivation:** Teach the learner to move in whatever direction.
* **Rewards:** +1 for correct answer
* **MaxTime**: Len(Instructions) + 3 TIME_MOVE
* **Prerequisites:** repeating strings in context, "I do-X" construction
* **Teacher inputs:** Move forward.

### **Moving relative [G3][IMP]**

* **Description:** Learner is asked to move in a given relative direction (left or right).
* **Instructions:** Move (left|right).
* **Example:**
    * **Teacher:** Move left.
    * **Learner:** I turn left.
    * **Teacher:** You turned.
    * **Learner:** I move forward.
    * **Teacher:** You moved [+1].
* **Feedback to mistakes**:
* **Motivation:** Teach the learner to move in an arbitrary direction.
* **Rewards:** +1 for correct answer
* **MaxTime**: Len(Instructions) + 2 TIME_TURN + 2 TIME_MOVE
* **Timeout Message**: Generic "time is out" message.
* **Prerequisites:** G1, G2
* **Teacher inputs:** Move left, Move right.

### **Moving absolute [G4][IMP]**

* **Description:** Learner is asked to move in a given direction
* **Instructions:** You are facing $DIRECTION, move $DIRECTION.
* **Example:**
    * **Teacher:** You are facing east, move west.
    * **Learner:** I turn right.
    * **Teacher**: You turned.
    * **Learner:** I turn right.
    * **Teacher**: You turned.
    * **Learner:** I move forward.
    * **Teacher**: You moved. [+1]
* **Motivation:** Teach the learner to move in an arbitrary direction.
* **Rewards:** +1 for correct answer
* **MaxTime**: Len(Instructions) + 8 TIME_TURN + 4 TIME_MOVE
* **Timeout Message**: Generic "time is out" message.
* **Prerequisites:** G1, G2, G3?
* **Teacher inputs:** You are facing $DIRECTION, move $DIRECTION.

### **Pick up Task [G6][IMP]**

* **Description:** Learner is asked to pick up an object it has at its feet.
* **Instructions:** I have placed a O where you are. Pick up the O.
* **Example:**
    * **Teacher:** I have placed an apple where you are. Pick up the apple.
    * **Learner:** I pick up the apple.
    * **Teacher:** You picked up the apple [+1].
* **Motivation:** Teach the learner how to pick up things
* **Rewards:** +1 for correct answer
* **MaxTime**: Len(Instructions) + TIME_PICK
* **Timeout Message**: Generic "time is out" message.
* **Prerequisites:**
* **Teacher inputs:**

### **Pick up in front Task [G7][IMP]**

* **Description:** Learner is asked to pick up an object it has N steps forward in front of it.
* **Instructions:** There is a[n] O N steps forward. Pick up the O.
* **Example:**
    * **Teacher:** There is an apple in front of you. Pick up the apple.
    * **Learner:** I pick up the apple.
    * **Teacher:** There in no apple here.
    * **Learner:** I move forward.
    * **Teacher:** You moved.
    * **Learner:** I pick up the apple.
    * **Teacher:** You picked up the apple [+1].
* **Motivation:** Teach the learner how to pick up things
* **Rewards:** +1 for correct answer
* **MaxTime**: Len(Instructions) + 4 TIME_LOOK +  2 * MAX_N * TIME_MOVE + 3 TIME_PICK
* **Timeout Message**: Generic "time is out" message.
* **Prerequisites:**
* **Teacher inputs:**

### **Pick up around Task [G8][IMP]**

* **Description:** Learner is asked to pick up an object it has around it.
* **Instructions:** There is a[n] O DIR from you. Pick up the O.
* **Example:**
    * **Teacher:** There is an apple west you. Pick up the apple.
    * **Learner:** I turn right.
    * **Teacher:** You turned.
    * **Learner:** I move forward.
    * **Teacher:** You moved.
    * **Learner:** I pick up the apple.
    * **Teacher:** You picked up the apple [+1].
* **Motivation:** Combines previous abilities (picking up and turning). Also, for the learner to be the most efficient, it will have to remember the last direction it was looking at.
* **Rewards:** +1 for correct answer
* **MaxTime**: Len(Instructions) + 4 TIME_LOOK +  TIME_MOVE + 3 TIME_PICK
* **Timeout Message**: Generic "time is out" message.
* **Prerequisites:**
* **Teacher inputs:**

### **Giving [G9][IMP]**

* **Description:** Learner is asked to give an object to the teacher
* **Instructions:** I gave you an O. Give it back to me by saying "I give you an O".
* **Example:**
    * **Teacher:** I gave you an apple. Give it back to me by saying "I give you an apple".
    * **Learner:** I give you an apple.
    * **Teacher:** You gave me an apple. [+1].
* **Motivation:** Teach the learner how to give things to the teacher. Later this will be useful to ask it to give you N objects.
* **Rewards:** +1 for correct answer
* **MaxTime**:
* **Timeout Message**: Generic "time is out" message.
* **Prerequisites:**
* **Teacher inputs:**

### **Pick up around and give [G10][IMP]**

* **Description:** Learner is asked to pick up and object and hand it to the teacher
* **Instructions:** There is an O DIR of you. Pick up the O and give it to me.
* **Example:**
    * **Teacher:** There is an apple west you. Pick up the apple and give it to me.
    * **Learner:** I turn right.
    * **Teacher:** You turned.
    * **Learner:** I move forward.
    * **Teacher:** You moved.
    * **Learner:** I pick up the apple.
    * **Teacher:** You picked up the apple.
    * **Learner:** I give you an apple.
    * **Teacher:** You gave me an apple.
* **Motivation:** Teach the learner how to find things near it.
* **Rewards:** +1 for correct answer
* **MaxTime**:
* **Timeout Message**: Generic "time is out" message.
* **Prerequisites:**
* **Teacher inputs:**

### **Pick up around many and give [G12]**

* **Description:** Learner is asked to pick up and object and hand it to the teacher
* **Instructions:** There is a[n] O1, a[n] O2, … a[n] On near you. Pick them up and give them to me.
* **Example:**
    * **Teacher:** There is an apple and a banana near you. Pick up them up and give them to me.
    * **Learner:** I turn right.
    * **Teacher:** You turned.
    * **Learner:** I move forward.
    * **Teacher:** You moved.
    * **Learner:** I pick up the apple.
    * **Teacher:** You picked up the apple.
    * **Learner:** I turn right.
    * **Teacher:** You turned.
    * **Learner:** I move forward.
    * **Teacher:** You moved.
    * **Learner:** I pick up the banana.
    * **Teacher:** You picked up the banana.
    * **Learner:** I give you an apple.
    * **Teacher:** You gave me an apple.
    * **Learner:** I give you a banana.
    * **Teacher:** You gave me a banana [+1].
* **Motivation:** Combines enumeration skills and counting with picking up and giving.
* **Rewards:** +1 for correct answer
* **MaxTime**:
* **Timeout Message**: Generic "time is out" message.
* **Prerequisites:**
* **Teacher inputs:**

### **Counting in inventory [G13][IMP]**

* **Description:** The learner has to tell how many objects of a type it has
* **Instructions:** How many Os do you have?
* **Example:**
    * **Teacher:** How many apples do you have?
    * **Learner:** two.
    * **Teacher**: No, you have one. [0]
* **Motivation:** Teach the learner to count and memorize the amount of objects in its inventory. Problem: it's much easier just to try one, two, three...
* **Rewards:** +1 for correct answer
* **MaxTime**:
* **Timeout Message**: Generic "time is out" message.
* **Prerequisites:**
* **Teacher inputs:**

### **Counting in inventory with giving [G14][IMP]**

* **Description:** The learner has to tell how many objects of a type it has
* **Instructions:** How many O do you have? … I gave you another O. How many O do you have? Give me an O. How many O do you have?.
* **Example:**
    * **Teacher:** How many apples do you have?
    * **Learner:** two.
    * **Teacher:** I gave you another apple. How many apples do you have?
    * **Learner:** three.
    * **Teacher:** Give me an apple.
    * **Learner:** I give you an apple.
    * **Teacher:** You gave me an apple. How many apples do you have?
    * **Learner:** two.
* **Motivation:** Teach the learner to keep track of the items in its inventory in relation to the actions it performs.
* **Rewards:** +1 for correct answer
* **MaxTime**:
* **Timeout Message**: Generic "time is out" message.
* **Prerequisites:**
* **Teacher inputs:**
