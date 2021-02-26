#include <stdint.h>

int64_t __attribute__ ((noinline)) func_omega2(void) {
	return 0;
}

int64_t __attribute__ ((noinline)) func_omega(void) {
	return func_omega2();
}

int64_t __attribute__ ((noinline)) func_alpha4(int64_t a) {
	return a + 1;
}

int64_t __attribute__ ((noinline)) func_alpha3(int64_t a) {
	return a + func_alpha4(3);
}

int64_t __attribute__ ((noinline)) func_alpha2(int64_t a) {
    int64_t tmp = a;

	tmp = func_alpha3(tmp);

	return tmp;
}

int64_t __attribute__ ((noinline)) func_alpha(int64_t a) {
	int64_t tmp = a;
	int64_t tmp2 = 2 * a;

	tmp = func_alpha2(tmp + tmp2);

	return tmp;
}

int64_t __attribute__ ((noinline)) func_beta(int64_t a, int64_t b) {
	int64_t tmp = a + b;

	tmp = func_alpha(tmp);

	return tmp;
}

int64_t __attribute__ ((noinline)) func_gamma(int64_t a, int64_t b, int64_t c) {
	int64_t tmp = 0;

	tmp = func_alpha(tmp);
	tmp = func_beta(tmp, a);

	return tmp + a + b + c;
}

int64_t __attribute__ ((noinline)) func_delta(int64_t a, int64_t b, int64_t c, int64_t d) {
	int64_t tmp = 0;

	tmp += func_alpha(a);
	tmp += func_beta(a, b);
	tmp += func_gamma(a, b, c);

	return tmp + a + b + c + d;
}

int64_t __attribute__ ((noinline)) func_epsilon(int64_t a, int64_t b, int64_t c, int64_t d, int64_t e) {
	int64_t tmp = 0;

	tmp += func_alpha(a);
	tmp += func_beta(a, b);
	tmp += func_gamma(a, b, c);
	tmp += func_delta(a, b, c, d);

	return tmp + a + b + c + d + e;
}

int64_t __attribute__ ((noinline)) rec_xi(int64_t a) {
	if (a < 10) {
		a++;
	}

	return rec_xi(a);
}

int64_t rec_psi(int64_t a);

int64_t __attribute__ ((noinline)) rec_phi(int64_t a) {
	if (a < 10) {
		return rec_psi(a + 1);
	}

	return a;
}

int64_t __attribute__ ((noinline)) rec_chi(int64_t a) {
	return rec_phi(a + 1);
}

int64_t __attribute__ ((noinline)) rec_psi(int64_t a) {
	return rec_chi(a + 1);
}

int64_t main(int argc, int** argv) {
	int64_t a;
	int64_t (*fp)(int64_t a);

	a = func_omega();
	a = func_epsilon(a, a, a, a, a);
	a = rec_psi(a);

	if (a < 10) {
		fp = &rec_phi;
	} else {
		fp = &func_alpha;
	}

	a = fp(a);
	a += rec_xi(a);
	a += rec_xi(a);

	return a + 1;
}
