"""
Test listings — simulated active listings in the system.
Some match test emails, some don't (to test auto-create logic).
"""

TEST_LISTINGS = [
    {
        "id": "a1b2c3d4-1111-2222-3333-444455556666",
        "address_line1": "Crofton Road",
        "city": "London",
        "postcode": "SE4 1AF",
        "listing_reference": None,
        "monthly_rent": 1500,
    },
    {
        "id": "b2c3d4e5-2222-3333-4444-555566667777",
        "address_line1": "Pemberton Gardens",
        "city": "London",
        "postcode": "N19 5RR",
        "listing_reference": None,
        "monthly_rent": 1650,
    },
    {
        "id": "c3d4e5f6-3333-4444-5555-666677778888",
        "address_line1": "Highbury Grove",
        "city": "London",
        "postcode": "N5 2AG",
        "listing_reference": "HBG-01",
        "monthly_rent": 1800,
    },
    {
        "id": "d4e5f6g7-4444-5555-6666-777788889999",
        "address_line1": "Caledonian Road",
        "city": "London",
        "postcode": "N7 9RN",
        "listing_reference": None,
        "monthly_rent": 1400,
    },
    {
        "id": "e5f6g7h8-5555-6666-7777-888899990000",
        "address_line1": "Elm Park Gardens",
        "city": "London",
        "postcode": "SW10 9QF",
        "listing_reference": "EPG-42",
        "monthly_rent": 2200,
    },
    {
        "id": "f6g7h8i9-6666-7777-8888-999900001111",
        "address_line1": "Lordship Lane",
        "city": "London",
        "postcode": "SE22 8HN",
        "listing_reference": None,
        "monthly_rent": 1550,
    },
    {
        "id": "g7h8i9j0-7777-8888-9999-000011112222",
        "address_line1": "Stroud Green Road",
        "city": "London",
        "postcode": "N4 3EF",
        "listing_reference": None,
        "monthly_rent": 1400,
    },
    {
        "id": "h8i9j0k1-8888-9999-0000-111122223333",
        "address_line1": "Blackstock Road",
        "city": "London",
        "postcode": "N5 1EN",
        "listing_reference": None,
        "monthly_rent": 1350,
    },
    {
        "id": "i9j0k1l2-9999-0000-1111-222233334444",
        "address_line1": "Mountgrove Road",
        "city": "London",
        "postcode": "N5 2LT",
        "listing_reference": None,
        "monthly_rent": 1200,
    },
    {
        "id": "j0k1l2m3-0000-1111-2222-333344445555",
        "address_line1": "Seven Sisters Road",
        "city": "London",
        "postcode": "N7 6AG",
        "listing_reference": None,
        "monthly_rent": 1350,
    },
]
