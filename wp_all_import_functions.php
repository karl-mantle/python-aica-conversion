<?php
declare(strict_types=1);

function get_user_id_by_full_name(string $full_name): int {
    $full_name = trim($full_name);

    if ($full_name === '') {
        return 0;
    }

    $users = get_users([
        'search'         => $full_name,
        'search_columns' => ['display_name'],
        'number'         => 1,
        'fields'         => ['ID'],
    ]);

    if (!empty($users)) {
        return (int) $users[0]->ID;
    }

    return 0;
}