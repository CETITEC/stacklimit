// SPDX-FileCopyrightText: 2022 CETITEC GmbH <https://www.cetitec.com>
//
// SPDX-License-Identifier: GPL-2.0-or-later

#include <stdint.h>

void __attribute__ ((noinline)) swap(int* list, int i, int j) {
    int temp = list[i];
    list[i] = list[j];
    list[j] = temp;
}

void __attribute__ ((noinline)) bubble_sort(int* list, int size) {
    for (int i = size; i > 1; i--) {
        for (int j = 0; j < i - 1; j++) {
            if (list[j] > list[j+1]) {
                swap(list, j, j+1);
            }
        }
    }
}

int main(int argc, int** argv) {
    int list[] = {1, 8, 3, 100, 88, 2};

    bubble_sort(list, 6);

    return 0;
}
