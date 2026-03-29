"""
Test emails — realistic, fuzzy applicant emails.
Each email has an 'expected' dict for automated comparison.
"""

TEST_EMAILS = [
    # -----------------------------------------------------------------------
    # 0: Initial interest — casual, short, no details
    # -----------------------------------------------------------------------
    {
        "sender_name": "j.morris82",
        "subject": "hi about the flat on Crofton Road",
        "body": (
            "hiya, saw your ad for the flat on crofton road in lewisham. "
            "is it still available? me and my girlfriend are looking to move "
            "in around august. cheers, Jamie Morris"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "initial_interest",
            "full_name": "Jamie Morris",
            "mentioned_rent": None,
        },
    },
    # -----------------------------------------------------------------------
    # 1: Initial interest — Rightmove forwarded enquiry with rent
    # -----------------------------------------------------------------------
    {
        "sender_name": None,
        "subject": "Fwd: New enquiry about Pemberton Gardens, London",
        "body": (
            "---------- Forwarded message ---------\n"
            "From: noreply@rightmove.co.uk\n"
            "Date: Mon, 24 Mar 2026\n"
            "Subject: New enquiry about Pemberton Gardens, London\n"
            "To: agent@example.com\n\n"
            "You have a new enquiry from Rightmove\n\n"
            "Property: Pemberton Gardens, London, N19\n"
            "Asking rent: £1,650 pcm\n\n"
            "Enquiry from:\n"
            "Name: Aisha Begum\n"
            "Email: aisha.b99@gmail.com\n"
            "Telephone: 07412 345678\n\n"
            "Message:\n"
            "Hi, I'm interested in this property, could I book a viewing please? "
            "I work as an NHS nurse full time. Thanks, Aisha"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "initial_interest",
            "full_name": "Aisha Begum",
            "mentioned_rent": 1650,
        },
    },
    # -----------------------------------------------------------------------
    # 2: Viewing request — clear request to view
    # -----------------------------------------------------------------------
    {
        "sender_name": "Marcus Johnson",
        "subject": "Re: Highbury Grove flat",
        "body": (
            "Hi there,\n\n"
            "Thanks for getting back to me. I'd love to come and see the flat "
            "on Highbury Grove if possible. Would Saturday morning work? "
            "I can be flexible on times.\n\n"
            "Best,\nMarcus"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "viewing_request",
            "full_name": "Marcus Johnson",
            "mentioned_rent": None,
        },
    },
    # -----------------------------------------------------------------------
    # 3: Document submission — payslip attached, casual email
    # -----------------------------------------------------------------------
    {
        "sender_name": "Priya Sharma",
        "subject": "Documents for Caledonian Road",
        "body": (
            "Hi,\n\nplease find my payslip and bank statement attached as requested.\n\n"
            "Kind regards,\nPriya"
        ),
        "attachments": ["payslip_march_2026.pdf", "hsbc_statement_feb.pdf"],
        "expected": {
            "email_phase": "document_submission",
            "full_name": "Priya Sharma",
            "mentioned_rent": None,
        },
    },
    # -----------------------------------------------------------------------
    # 4: Document submission — no mention in body, but filenames give it away
    # -----------------------------------------------------------------------
    {
        "sender_name": "Tom Blackwood",
        "subject": "Re: Elm Park Gardens application",
        "body": (
            "As discussed, please see attached.\n\nTom"
        ),
        "attachments": ["p60_2025.pdf", "barclays_bank_statement_jan2026.pdf", "passport_scan.jpg"],
        "expected": {
            "email_phase": "document_submission",
            "full_name": "Tom Blackwood",
            "mentioned_rent": None,
        },
    },
    # -----------------------------------------------------------------------
    # 5: Initial interest — messy email, income mentioned (not rent),
    #    vague address, typos
    # -----------------------------------------------------------------------
    {
        "sender_name": "daveT1990",
        "subject": "enquiry about your property in crouch end",
        "body": (
            "hi there im interested in the 2 bed in crouch end near the broadway. "
            "i earn about 3200 a month and work as a plumber. would be me and my "
            "son (hes 6). we dont have any pets. when can we see it? "
            "thanks dave thompson"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "initial_interest",
            "full_name": "Dave Thompson",
            "mentioned_rent": None,  # 3200 is income, not rent
        },
    },
    # -----------------------------------------------------------------------
    # 6: Post-viewing follow-up
    # -----------------------------------------------------------------------
    {
        "sender_name": "Sarah Chen",
        "subject": "Following up - Lordship Lane viewing",
        "body": (
            "Hi,\n\n"
            "I viewed the flat on Lordship Lane last Thursday and really liked it. "
            "I'd like to go ahead with my application if it's still available. "
            "What documents do you need from me?\n\n"
            "Best wishes,\nSarah Chen"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "post_viewing",
            "full_name": "Sarah Chen",
            "mentioned_rent": None,
        },
    },
    # -----------------------------------------------------------------------
    # 7: Offer — wants to secure the property
    # -----------------------------------------------------------------------
    {
        "sender_name": "Daniel Okafor",
        "subject": "Offer for Stroud Green Road flat",
        "body": (
            "Dear Sir/Madam,\n\n"
            "Following our viewing yesterday, I would like to make a formal offer "
            "for the one bedroom flat on Stroud Green Road at the asking rent of "
            "£1,400 per month. I am happy to pay 6 months upfront if that helps "
            "secure the property.\n\n"
            "I can provide all references and documents immediately.\n\n"
            "Kind regards,\nDaniel Okafor"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "offer",
            "full_name": "Daniel Okafor",
            "mentioned_rent": 1400,
        },
    },
    # -----------------------------------------------------------------------
    # 8: Questionnaire reply — short structured answers
    # -----------------------------------------------------------------------
    {
        "sender_name": "Emma Walsh",
        "subject": "Re: Application questions - Blackstock Road",
        "body": (
            "Hi, answers below:\n\n"
            "Full name: Emma Louise Walsh\n"
            "Date of birth: 12/05/1994\n"
            "Current address: 28 Romford Road, London E7\n"
            "Employer: Deloitte LLP\n"
            "Annual salary: £48,000\n"
            "Tenancy start: 1st August 2026\n"
            "Number of occupants: 1\n"
            "Pets: No\n"
            "Smoker: No\n\n"
            "Let me know if you need anything else.\n"
            "Emma"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "questionnaire_reply",
            "full_name": "Emma Walsh",
            "mentioned_rent": None,  # 48000 is salary, not rent
        },
    },
    # -----------------------------------------------------------------------
    # 9: Zoopla forwarded enquiry — different platform format
    # -----------------------------------------------------------------------
    {
        "sender_name": None,
        "subject": "Fwd: New enquiry from Zoopla - Mountgrove Road, N5",
        "body": (
            "---------- Forwarded message ---------\n"
            "From: noreply@zoopla.co.uk\n"
            "Date: Tue, 25 Mar 2026\n"
            "Subject: New enquiry from Zoopla - Mountgrove Road, N5\n"
            "To: agent@example.com\n\n"
            "You have received a new enquiry via Zoopla\n\n"
            "Property: Mountgrove Road, London, N5\n"
            "Asking rent: £1,200 pcm\n\n"
            "Enquiry from:\n"
            "Name: Rachel Adeyemi\n"
            "Email: rachel.ade@outlook.com\n"
            "Phone: 07555 123456\n\n"
            "Message:\n"
            "Hi, I saw your listing and I'm very interested. Could I arrange "
            "a viewing? Thanks, Rachel"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "initial_interest",
            "full_name": "Rachel Adeyemi",
            "mentioned_rent": 1200,
        },
    },
    # -----------------------------------------------------------------------
    # 10: Tricky — mentions both income AND rent, fuzzy writing
    # -----------------------------------------------------------------------
    {
        "sender_name": "mikeyP",
        "subject": "about the place on seven sisters rd",
        "body": (
            "hey, i saw the 1 bed on seven sisters road listed at 1350 a month. "
            "i make about 45k a year working in IT so i can definitely afford it. "
            "its just me, no pets or anything. when can i come have a look?\n\n"
            "mike peterson"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "initial_interest",
            "full_name": "Mike Peterson",
            "mentioned_rent": 1350,
        },
    },
    # -----------------------------------------------------------------------
    # 11: Unknown / off-topic — not a rental enquiry
    # -----------------------------------------------------------------------
    {
        "sender_name": "Karen Plumbing Services",
        "subject": "Annual boiler service reminder",
        "body": (
            "Dear Customer,\n\n"
            "This is a reminder that your annual boiler service is due. "
            "Please call us on 020 7123 4567 to book an appointment.\n\n"
            "Kind regards,\nKaren's Plumbing & Heating Ltd"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "unknown",
            "full_name": None,
            "mentioned_rent": None,
            "property_reference": None,
        },
    },
]
