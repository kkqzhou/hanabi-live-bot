from tes_helpers import run_simple_test
import card
from collections import Counter

def create_empathies(empathy_tuples):
    empathies = [card.Empathy("No Variant") for _ in range(5)]
    for i, tuples in enumerate(empathy_tuples):
        empathies[i].set_empathy(tuples, reset_inferences=False)
    return empathies

def test_get_locked_identities():    
    tests = [
        (
            (
                create_empathies([
                    {(3,3)},
                    {(3,3)},
                    {(0,3), (1,3), (2,3), (3,3), (4,3)},
                    {(0,3), (1,3), (2,3), (3,3), (4,3)},
                    {(0,3), (1,3), (2,3), (3,3), (4,3)}
                ]),
                {}
            ),
            [card.LockedIdentity([0,1], Counter({(3,3): 2}))]
        ),
        (
            (
                create_empathies([
                    {(1,2), (3,2), (1,5)},
                    {(1,2), (3,2), (1,5)},
                    {(1,5)},
                    {(1,2), (3,2)},
                    {(0,3), (1,3), (2,3), (3,3), (4,3)}
                ]),
                {(1,2): 1}
            ),
            [card.LockedIdentity([2], Counter({(1,5): 1})), card.LockedIdentity([0,1,3], Counter({(3,2): 2, (1,2): 1}))]
        ),
        (
            (
                create_empathies([
                    {(1,5), (2,5), (3,5)},
                    {(3,5), (4,5), (0,5)},
                    {(0,5)},
                    {(1,5), (2,5)},
                    {(3,5), (4,5)}
                ]),
                {}
            ),
            [
                card.LockedIdentity([2], Counter({(0,5): 1})),
                card.LockedIdentity([0,3], Counter({(1,5): 1, (2,5): 1})),
                card.LockedIdentity([1,4], Counter({(3,5): 1, (4,5): 1}))
            ]
        ),
        (
            (
                create_empathies([
                    {(0,5), (1,5), (2,5), (3,5), (4,5)},
                    {(1,5), (2,5), (3,5), (4,5)},
                    {(1,5), (2,5), (3,5), (4,5)},
                    {(1,5), (2,5), (3,5), (4,5)},
                    {(1,5), (2,5), (3,5), (4,5)}
                ]),
                {}
            ),
            [
                card.LockedIdentity([0], Counter({(0,5): 1})),
                card.LockedIdentity([1,2,3,4], Counter({(1,5): 1, (2,5): 1, (3,5): 1, (4,5): 1}))
            ]
        ),
        (
            (
                create_empathies([
                    {(0,5), (1,5)},
                    {(1,5), (3,5), (4,5)},
                    {(1,5), (3,5), (4,5)},
                    {(3,1), (2,5)},
                    {(3,1), (3,2)}
                ]),
                {(1,5): 1, (3,1): 3}
            ),
            [
                card.LockedIdentity([0], Counter({(0,5): 1})),
                card.LockedIdentity([3], Counter({(2,5): 1})),
                card.LockedIdentity([1,2], Counter({(3,5): 1, (4,5): 1}))
            ]
        ),
    ]
    run_simple_test(card.get_locked_identities, tests)

if __name__ == "__main__":
    test_get_locked_identities()