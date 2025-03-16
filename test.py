# Team info
away = False
OPPONENT = "Sakaryaspor"

if away:
    match = f"{OPPONENT} - Kocaelispor"
    title = "Deplasman satılan bilet"
else:
    match = f"Kocaelispor - {OPPONENT}"
    title = "Satılan bilet"
    
    total_occupied_seats = 31827
    total_available_seats = 0
    home_total = 31827
    
    total_count = total_occupied_seats + total_available_seats
    full_blocks = home_total - total_count
    total_occupied_seats += full_blocks
    total_available_seats = home_total - total_occupied_seats
    occupancy_rate = (total_occupied_seats / home_total) * 100 if total_count > 0 else 0

    bar_length = int(occupancy_rate / 6.25)
    empty_length = 16 - bar_length
    occupancy_bar = "█" * bar_length + "░" * empty_length

    output = f"{match}\n{occupancy_bar} %{occupancy_rate:.2f}\n{title}: {total_occupied_seats} / {home_total}"
    if occupancy_rate == 100:
        output += "\n🔥 KAPALI GİŞE"
    else:
        output += f" (Kalan: {total_available_seats})"
    print(output)