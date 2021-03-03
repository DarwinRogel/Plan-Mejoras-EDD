{
    "name": "Plan Mejoras de la Evaluación al Desempeño Docente",
    "description":"Módulo de software para el Plan Mejoras de la Evaluación al Desempeño Docente para la CIS/C",
    "author": "Darwin Rogel Rivera - Robin Cordova Alvarado",

    "summary": """
        Módulo de Software que permite la optimización técnica del Plan Mejoras de la EDD en la CIS/C de la Universidad Nacional de Loja
        """,

    "website": "https://unl.edu.ec/",

    "category": "Seguimiento",

    "version": "1.0",
    "depends": ["base", "mail"],
    "images": ['static/description/CIS.png'],
    "data": [
        "data/quotation_expiration_cron.xml",
        "data/mail_template_inicializarPM.xml",
        "security/res_groups.xml",
        "security/ir_rule.xml",
        "security/ir_model_access.xml",
        "report/template.xml",
        "report/report.xml",
        "views/views.xml"
    ]
}