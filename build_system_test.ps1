param(
[string]$PCName
);

Invoke-Command -Computername $PCName -ScriptBlock { C:\PROGRA~2\ODOO11~1.0\nssm\win64\nssm.exe set odoo-server-11.0 AppParameters "C:\PROGRA~2\ODOO11~1.0\server\odoo-bin -d dbv11_recruitment -i recruitment_ads,report_xlsx,sync_ldap_ads" }
