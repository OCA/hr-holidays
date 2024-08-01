To use this module, you need to:

1. Go to Time Off app > Configuration > Public Holidays
2. Create a Public Holiday without State with name *Local Holiday*
3. Create an *Employee 1* and set his Work Address in the same State than your *Local Holiday*
4. Create an *Employee 2* and set his Work Address in other State than your *Local Holiday*
5. Go to Time Off > Overview and check the grey background is only on *Employee 1* on the days used in *Local Holiday*
6. Create a Time Off for *Employee 1* that involves *Local Holiday* and check the days used are computed correctly
7. Create a Time Off for *Employee 2* that involves *Local Holiday* and check the days used are computed correctly (more days than the Time Off of *Employee 1*)
8. Check both Employee Calendar views from the Employee form to view the grey background on Local and Public Holidays.

If you have installed Attendances and Contracts apps, and create attenances for both employees on the *Local Holiday* you can also check Extra Hours are computed correctly in both employees.
