def inject_attack(asset, attack):
    if asset.endswith(".pdf"):
        return inject_attack_into_pdf(asset, attack)
    
    if asset.endswith(".html"):
        return inject_attack_into_html(asset, attack)
    
    if asset.endswith(".txt") and asset.contains("email"):
        return inject_attack_into_email(asset, attack)
    
    if asset.endswith(".ics"):
        return inject_attack_into_calendar(asset, attack)

    if asset.endswith(".md") and asset.contains("claude"):
        return inject_attack_into_claude_markdown(asset, attack)
    