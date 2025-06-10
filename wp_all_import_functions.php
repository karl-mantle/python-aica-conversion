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

// don't use these anymore!! quicker to preprocess in python! ^^ can't do the above outside of WP though

function get_post_title_if_blank(string $post_title, string $namea, string $nameb, string $tombstone): string {
    // if ($post_title !=== '') { // should this be !empty($post_title)?
    if (!empty($post_title)) {
        return $post_title;
    } else {
        // trim spaces from end of $namea, $nameb and $tombstone
        $namea = trim($namea);
        $nameb = trim($nameb);
        $tombstone = trim($tombstone);

        // concatenate the 3 strings like `${namea} ${tombstone} ${nameb}`
        $parts = array_filter([$namea, $tombstone, $nameb], function($part) {
            return $part !== '';
        });
        return implode(' ', $parts);
    }
}

function get_client_name(string $namea, string $prospectname): string {
    return !empty(trim($namea)) ? trim($namea) : trim($prospectname);
}

function get_visibility_from_confidential(string $confidential): string {
    return ($confidential === '1') ? 'public' : 'hidden';
}

function get_date_from_dates(string $completeddate, string $engagedmandatedate, string $projectstartdate): string {
    if (!empty($completeddate)) {
        return $completeddate;
    } elseif (!empty($engagedmandatedate)) {
        return $engagedmandatedate;
    } elseif (!empty($projectstartdate)) {
        return $projectstartdate;
    } else {
        return '1970-01-01';
    }
}

// example for wp all import - [get_date_from_dates({completeddate[1]},{engagedstartdate[1]},{projectstartdate[1]})]