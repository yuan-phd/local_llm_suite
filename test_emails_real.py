"""
Real test emails — from Test-Emails-Applicants-01.
These are actual emails the system would receive, with realistic messiness.
"""

REAL_TEST_EMAILS = [
    # -----------------------------------------------------------------------
    # 0: James Bond — payslip attached, very short body
    # -----------------------------------------------------------------------
    {
        "sender_name": "James Bond",
        "subject": "Regarding Mountview Street",
        "body": (
            "Hi, please find my payslip attached. Kind regards, James Bond"
        ),
        "attachments": ["payslip_march2026.pdf"],
        "expected": {
            "email_phase": "document_submission",
            "full_name": "James Bond",
            "mentioned_rent": None,
        },
    },
    # -----------------------------------------------------------------------
    # 1: Rightmove forwarded — Sarah Johnson, NHS nurse
    # -----------------------------------------------------------------------
    {
        "sender_name": None,
        "subject": "Fwd: New enquiry about Oakwood Drive, London",
        "body": (
            "---------- Forwarded message ---------\n"
            "From: noreply@rightmove.co.uk\n"
            "Date: Wed, 18 Mar 2026\n"
            "Subject: New enquiry about Oakwood Drive, London\n"
            "To: gjetertaske@gmail.com\n\n"
            "You have a new enquiry from Rightmove\n\n"
            "Property: Oakwood Drive, London, SW1A\n"
            "Asking rent: £1,800 pcm\n\n"
            "Enquiry from:\n"
            "Name: Sarah Johnson\n"
            "Email: propswift.t1@outlook.com\n"
            "Telephone: 07700 900123\n\n"
            "Message:\n"
            "Hi, I'm very interested in this property. I'm a nurse working "
            "full-time at NHS and earn about £42,000 per year. I'd ideally "
            "like to move in by 1st July 2026. It would be myself and my "
            "partner. Could we arrange a viewing please? Thank you, Sarah"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "initial_interest",
            "full_name": "Sarah Johnson",
            "mentioned_rent": 1800,
        },
    },
    # -----------------------------------------------------------------------
    # 2: Victoria Lane — Emma, barista, part-time, short
    # -----------------------------------------------------------------------
    {
        "sender_name": "Emma",
        "subject": "Enquiry about Victoria Lane",
        "body": (
            "Hi, I saw your listing for Victoria Lane at £1,200 per month. "
            "I'm interested in renting it. I work part-time as a barista. "
            "When would viewings be available? Thanks, Emma"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "initial_interest",
            "mentioned_rent": 1200,
        },
    },
    # -----------------------------------------------------------------------
    # 3: Bond Road — Test Person A, Goldman Sachs, £6k/month
    # -----------------------------------------------------------------------
    {
        "sender_name": "Test Person A",
        "subject": "Enquiry about Bond Road, Islington",
        "body": (
            "Hi, I earn £6,000 per month gross. I'm a full-time permanent "
            "employee at Goldman Sachs. Looking to move in July 2026 with "
            "my partner. Kind regards, Test Person A"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "initial_interest",
            "full_name": "Test Person A",
            "mentioned_rent": None,  # 6000 is income, not rent
        },
    },
    # -----------------------------------------------------------------------
    # 4: Hamilton Road — Test Person B, self-employed, £42k annual
    # -----------------------------------------------------------------------
    {
        "sender_name": "Test Person B",
        "subject": "Enquiry about Hamilton Road, Camden",
        "body": (
            "Hi, my annual salary is £42,000 before tax. I'm self-employed. "
            "I'd like to move in ASAP. It'll be just me. "
            "Regards, Test Person B"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "initial_interest",
            "full_name": "Test Person B",
            "mentioned_rent": None,  # 42000 is salary
        },
    },
    # -----------------------------------------------------------------------
    # 5: Bellaville Road — Test Person C, contractor, £450/day
    # -----------------------------------------------------------------------
    {
        "sender_name": "Test Person C",
        "subject": "Enquiry about Bellaville Road, Hackney",
        "body": (
            "Hi, I'm a contractor earning £450 per day, 5 days a week. "
            "Looking for a 12-month tenancy starting September 2026. "
            "2 adults, 1 child. Thanks, Test Person C"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "initial_interest",
            "full_name": "Test Person C",
            "mentioned_rent": None,  # 450 is daily rate
        },
    },
    # -----------------------------------------------------------------------
    # 6: South Ringsong Road — Test Person D, teacher, £3,500
    # -----------------------------------------------------------------------
    {
        "sender_name": "Test Person D",
        "subject": "Enquiry about South Ringsong Road, Brixton",
        "body": (
            "Hello, I earn £3,500 and I work as a teacher. When can I view "
            "the property? I'd like to move in May 2026. "
            "Best, Test Person D"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "initial_interest",
            "full_name": "Test Person D",
            "mentioned_rent": None,  # 3500 is income
        },
    },
    # -----------------------------------------------------------------------
    # 7: Zoopla forwarded — Rachel Green, Elm Street Bristol
    # -----------------------------------------------------------------------
    {
        "sender_name": None,
        "subject": "Fwd: New enquiry from Zoopla - Elm Street, Bristol",
        "body": (
            "---------- Forwarded message ---------\n"
            "From: noreply@zoopla.co.uk\n"
            "Date: Thu, 19 Mar 2026\n"
            "Subject: New enquiry from Zoopla - Elm Street, Bristol\n"
            "To: gjetertaske@gmail.com\n\n"
            "You have received a new enquiry via Zoopla\n\n"
            "Property: Elm Street, Bristol, BS1\n"
            "Asking rent: £1,400 pcm\n\n"
            "Enquiry from:\n"
            "Name: Rachel Green\n"
            "Email: propswift.t3@outlook.com\n"
            "Phone: 07700 900456\n\n"
            "Message:\n"
            "Hi, I saw your listing on Zoopla and I'm very interested. "
            "Could I arrange a viewing please? Thanks, Rachel"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "initial_interest",
            "full_name": "Rachel Green",
            "mentioned_rent": 1400,
        },
    },
    # -----------------------------------------------------------------------
    # 8: Elm Street Bristol — Michael Taylor, very brief
    # -----------------------------------------------------------------------
    {
        "sender_name": "Michael Taylor",
        "subject": "Interested in Elm Street, Bristol",
        "body": (
            "Hi, I'm interested in the property on Elm Street in Bristol. "
            "Could you let me know more about it? Thanks, Michael Taylor"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "initial_interest",
            "full_name": "Michael Taylor",
            "mentioned_rent": None,
        },
    },
    # -----------------------------------------------------------------------
    # 9: Sarah Chen — detailed application reply, looks like questionnaire
    # -----------------------------------------------------------------------
    {
        "sender_name": "Sarah Chen",
        "subject": "Re: Your application for Elm Street, Bristol — Additional information needed",
        "body": (
            "Hi, my name's Sarah Chen. I make about forty-two thousand a year "
            "before tax. I'm a permanent employee at Barclays. It'll be me "
            "and my two kids moving in, hopefully by end of June. We'd want "
            "to stay at least 2 years. My mum can be guarantor if needed. "
            "No pets, non-smoker."
        ),
        "attachments": None,
        "expected": {
            "email_phase": "questionnaire_reply",
            "full_name": "Sarah Chen",
            "mentioned_rent": None,  # 42000 is salary
        },
    },
    # -----------------------------------------------------------------------
    # 10: David Thompson — payslip attached, Maple Road Manchester
    # -----------------------------------------------------------------------
    {
        "sender_name": "David Thompson",
        "subject": "Documents for Maple Road, Manchester",
        "body": (
            "Hi, please find my payslip attached. Kind regards, David Thompson"
        ),
        "attachments": ["payslip_march_2026.pdf"],
        "expected": {
            "email_phase": "document_submission",
            "full_name": "David Thompson",
            "mentioned_rent": None,
        },
    },
    # -----------------------------------------------------------------------
    # 11: Post-viewing — Maple Road, no docs yet
    # -----------------------------------------------------------------------
    {
        "sender_name": None,
        "subject": "Re: Maple Road, Manchester",
        "body": (
            "Hi, I viewed the property last week and loved it. I'd like to "
            "proceed with my application. I'll send my payslip and bank "
            "statements separately."
        ),
        "attachments": None,
        "expected": {
            "email_phase": "post_viewing",
            "mentioned_rent": None,
        },
    },
    # -----------------------------------------------------------------------
    # 12: Parkside Avenue Leeds — accountant, £4k/month income
    # -----------------------------------------------------------------------
    {
        "sender_name": None,
        "subject": "Enquiry about Parkside Avenue, Leeds",
        "body": (
            "Hi, I'm interested in renting this property. I earn £4,000 per "
            "month and work as a full-time accountant. I'd like to move in "
            "by September 2026. It will be myself and my wife."
        ),
        "attachments": None,
        "expected": {
            "email_phase": "initial_interest",
            "mentioned_rent": None,  # 4000 is income
        },
    },
    # -----------------------------------------------------------------------
    # 13: Zoopla — Tom Clarke, Oak Lane Birmingham, delivery driver
    # -----------------------------------------------------------------------
    {
        "sender_name": None,
        "subject": "Fwd: New enquiry from Zoopla - Oak Lane, Birmingham",
        "body": (
            "---------- Forwarded message ---------\n"
            "From: noreply@zoopla.co.uk\n"
            "Date: Thu, 19 Mar 2026\n"
            "Subject: New enquiry from Zoopla - Oak Lane, Birmingham\n"
            "To: gjetertaske@gmail.com\n\n"
            "You have received a new enquiry via Zoopla\n\n"
            "Property: Oak Lane, Birmingham, B15\n"
            "Asking rent: £950 pcm\n\n"
            "Enquiry from:\n"
            "Name: Tom Clarke\n"
            "Email: propswift.a@outlook.com\n"
            "Phone: 07700 900789\n\n"
            "Message:\n"
            "Hi, I'm interested in this property. I work as a delivery "
            "driver and earn about £2,200 per month. Could I arrange a "
            "viewing? Thanks, Tom"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "initial_interest",
            "full_name": "Tom Clarke",
            "mentioned_rent": 950,
        },
    },
    # -----------------------------------------------------------------------
    # 14: Rightmove — Emma Wilson, Birch Close Leeds, nurse
    # -----------------------------------------------------------------------
    {
        "sender_name": None,
        "subject": "Fwd: New enquiry from Rightmove - Birch Close, Leeds",
        "body": (
            "---------- Forwarded message ---------\n"
            "From: noreply@rightmove.co.uk\n"
            "Date: Thu, 19 Mar 2026\n"
            "Subject: New enquiry - Birch Close, Leeds\n"
            "To: gjetertaske@gmail.com\n\n"
            "You have a new enquiry from Rightmove\n\n"
            "Property: Birch Close, Leeds, LS1\n"
            "Asking rent: £1,100 pcm\n\n"
            "Enquiry from:\n"
            "Name: Emma Wilson\n"
            "Email: propswift.t1@outlook.com\n"
            "Phone: 07700 900321\n\n"
            "Message:\n"
            "Hi, I'd love to view this property. I work full-time as a "
            "nurse. Thanks, Emma"
        ),
        "attachments": None,
        "expected": {
            "email_phase": "initial_interest",
            "full_name": "Emma Wilson",
            "mentioned_rent": 1100,
        },
    },
]
