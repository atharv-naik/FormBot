from gform import GForm, logger

if __name__ == '__main__':

    INFO = {
        'name': 'Alex Johnson',
        'email': 'alex.johnson@example.com',
        'id': 'REG-2025-001',
        'organization': 'Tech Research Labs',
        'ticket_type': ('Standard', 1),
        'registration_id': 'CONF-2025-STD-001',
        'sessions': [
            'AI in Healthcare',
            'Cloud Computing Trends',
            'Quantum Computing 101',
            'Data Privacy and Ethics',
        ]
    }

    # Example form data structure
    form_data = {
        'text': {
            'Email': {
                'types': ['text', 'email'],
                'response': INFO['email'],
            },
            'Full Name': {
                'types': ['text'],
                'response': INFO['name'],
            },
            'Registration ID': {
                'types': ['text'],
                'response': INFO['id'],
            },
            'Organization': {
                'types': ['text'],
                'response': INFO['organization'],
            },
            'Ticket Reference': {
                'types': ['text'],
                'response': INFO['registration_id'],
            },
        },
        'checkbox': {
            'Preferred Sessions': {
                'choices': [
                    INFO['sessions'][0],
                    INFO['sessions'][2],
                ],
            },
        },
        'radio': {
            'Ticket Type': {
                'choice': INFO['ticket_type'][0],
                'choice_num': INFO['ticket_type'][1],
            },
        },
    }

    gform = GForm()
    gform.create_mappings(form_data, exhaustive=False)
    t = gform.fill(
        url='https://forms.gle/z6wBJuZgUuUfbvzV7',
        submit=True,
    )
    logger.info(f"Time taken: {t:.2f} seconds") if t != -1 else None
