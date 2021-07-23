pragma solidity =0.7.6;
pragma abicoder v2;

import "hardhat/console.sol";

import "@uniswap/v3-periphery/contracts/libraries/OracleLibrary.sol";
import "@uniswap/v3-periphery/contracts/libraries/PoolAddress.sol";
import "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import "@uniswap/v3-periphery/contracts/interfaces/ISwapRouter.sol";
import "@uniswap/v3-periphery/contracts/interfaces/IQuoter.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./libraries/SafeUint128.sol";
import "./libraries/SafeMath32.sol";

contract BaseBot {
    // Administrator of the trading bot
    using SafeMath for uint256;

    address admin;

    ISwapRouter public constant uniswapRouter =
        ISwapRouter(0xE592427A0AEce92De3Edee1F18E0157C05861564);
    IQuoter public constant quoter =
        IQuoter(0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6);

    address public immutable uniswapV3Factory;
    address public immutable token0;
    address public immutable token1;
    uint24 public immutable defaultFee;

    address[] pendingSubscribers;

    address[] confirmedSubscribers;

    address poolAddress;

    enum SubscriptionStatus {
        PENDING,
        APPROVED
    }

    event UserSubscribed(address subscriberAddress);
    event SubscriptionConfirmed(address userAddress);
    event TestEvent(uint testNum);

    struct Subscriber {
        uint256 amount;
        SubscriptionStatus subscriptionStatus;
    }

    mapping(address => Subscriber) subscribers;

    constructor(
        address _uniswapV3Factory,
        address _token0,
        address _token1,
        uint24 _defaultFee
    ) {
        uniswapV3Factory = _uniswapV3Factory;
        token0 = _token0;
        token1 = _token1;
        defaultFee = _defaultFee;
        admin = msg.sender;

    }

    // ------------------------------- SUBSCRIPTION -------------------------------

    // @notice Request subscription to the bot with an amount of investment. This function does not transfer any investment to the admin
    // @param _investmentAmount This is the amount of money the user promises to send the admin
    function requestSubscription() external {
        // Make sure that the one calling this function is a user, not the admin
        require(msg.sender != admin, "Admin cannot subscribe to the bot");
        // Add the caller to the subscribers list, with status pending confirmation
        subscribers[msg.sender].subscriptionStatus = SubscriptionStatus.PENDING;
        emit UserSubscribed(msg.sender);
    }

    // @notice Called by the admin once a user sends money
    // Checks if the user has sent the amount of money it has promised to send. If she has, subscribes them to the bot.
    // Otherwise, the admin can pay back the amount using an external method
    function subscribeUser(address user) external {
        // Make sure that the one calling this function is the admin
        require(msg.sender == admin, "Only the admin can confirm subscription");
        // Check if the user has actually invested the money she hes promised to invest
        subscribers[user].subscriptionStatus = SubscriptionStatus.APPROVED;
        emit SubscriptionConfirmed(user);
    }

    // ------------------------------- TRADING -------------------------------

    // --------------------------- THE MAIN TRADING FUNCTION ---------------------------
    /// Trading

    // Called by the admin to make trading decisions.
    // Calls the functions for separate trading algorithms
    function trade(uint32 numOfPeriods, uint32 periodLength) public {
        // Make sure that the one who is calling the algorithm is the admin of the bot
        require(msg.sender == admin, "Only the admin can invoke trading");
        // The bot admin selects the trading algorithms secretly in the following way:
        // It calls the algorithms in all cases
        // If the first parameter passed to these functions are negative, this is an indicator that this algorithm is going to be used or not
        // This is checked in the algorithm function and the algorithm proceeds or does not proceed accordingly
        bollinger(numOfPeriods, periodLength);

        // Update the value of the amount of the money in the pool after trading. Of course, this should happen after
        // the trades are executed externally
    }

    // --------------------------- TRADING ALGORITHM: BOLLINGER ---------------------------
    // @notif Buy if (price < lower Bolliger band), sell if (price > upper Bolliger band) within certain thresholds
    //
    // Public parameters:
    // @param numOfPeriods number of periods, same as explained above
    // @param periodLength length of the periods for both EMAs, same as explained above
    //
    // Private parameters:
    // @private_param bollingerUpperBoundPct percentage the current price should be near the upper Bollinger band to trigger a sell signal
    // @private_param bollingerLowerBoundPct percentage the current price should be near the lower Bollinger band to trigger a buy signal
    function bollinger(uint32 numOfPeriods, uint32 periodLength)
        public
        returns (
            uint256[] memory pastPrices,
            uint256 movingAverage,
            uint256 stdDev
        )
    {
        require(
            admin == msg.sender,
            "Only the admin can invoke the trading algorithm"
        );
        // If the first parameter is negative, this is an indicator that this algorithm is going to be used or not
        require(numOfPeriods > 0);
        // Upper Bollinger Band=MA(TP,n) + m * σ[TP,n]
        // Lower Bollinger Band=MA(TP,n) − m * σ[TP,n]
        //      where:
        //      MA=Moving average
        //      TP (typical price)=(High+Low+Close)÷3
        //      n=Number of days in smoothing period (typically 20)
        //      m=Number of standard deviations (typically 2)
        //      σ[TP,n]=Standard Deviation over last n periods of TP
        (movingAverage, pastPrices) = sma(numOfPeriods, periodLength);
        stdDev = standardDev(pastPrices, movingAverage);
        // upperBollingerBand = movingAverage + 2 * stdDev;
        // lowerBollingerBand = movingAverage - 2 * stdDev;
        // if (currentPrice > (upperBollingerBand / 100) * (100 - bollingerUpperBoundPct)) {
        //     console.log("Selling token1");
        //     //swap(token1, token0, subscribers[msg.sender].amount);
        // } else if (currentPrice < (lowerBollingerBand / 100) * (100 + bollingerLowerBoundPct)) {
        //     console.log("Buying token1");
        //     //swap(token0, token1, subscribers[msg.sender].amount);
        // }
        // else: Hold
    }

    function test() public returns(uint32 val){
        val = 1111;
        emit TestEvent(1234567);
    }

    function getCurrentPrice() public returns (uint256 currentPrice) {
        if (poolAddress == address(0x0)) {
            poolAddress = PoolAddress.computeAddress(
                uniswapV3Factory,
                PoolAddress.getPoolKey(token0, token1, defaultFee)
            );
        }
        console.log(poolAddress);
        int256 twapTick = OracleLibrary.consult(poolAddress, 1);
        currentPrice = OracleLibrary.getQuoteAtTick(
            int24(twapTick), // can assume safe being result from consult()
            1,
            token0,
            token1
        );
    }

    function swap(
        address tokenIn,
        address tokenOut,
        uint256 amount
    ) public {
        require(
            ((tokenIn == token0 && tokenOut == token1) ||
                (tokenIn == token1 && tokenOut == token0)),
            "Input tokens are wrong."
        );
        // if (tokenIn == token0 && tokenOut == token1) {
        //     subscribers[msg.sender].balanceToken0 -= amount;
        //     subscribers[msg.sender].balanceToken1 += amount;
        // } else {
        //     subscribers[msg.sender].balanceToken1 -= amount;
        //     subscribers[msg.sender].balanceToken0 += amount;
        // }
        // console.log("Balance of token0 is % , token1 is %", subscribers[msg.sender].balanceToken0, subscribers[msg.sender].balanceToken1);
    }

    // Helper functions

    /// @notice Given a time period to look back into and the number of data points, calculates the
    /// Simple Moving Average (SMA) for token1 in terms of token0
    /// @return sma SMA, i.e. average of a number of past prices
    function sma(uint32 numOfPeriods, uint32 periodLength)
        public
        returns (uint256 sma, uint256[] memory priceAtTick)
    {
        // Calculate the time intervals to look behind untilSecondsAgo with numIntervals
        // Put this information into secondAgos for feeding into pool observation later
        uint32[] memory secondAgos = new uint32[](numOfPeriods + 1);
        for (uint32 i = 0; i < numOfPeriods; i++) {
            secondAgos[i] = SafeMath32.mul(periodLength, numOfPeriods - i);
        }

        // Get the Uniswap Pool for token0, token1, and defaultFee values
        IUniswapV3Pool pool = IUniswapV3Pool(poolAddress);
        (int56[] memory tickCumulatives, ) = pool.observe(secondAgos);

        // Calculate the Simple Moving Average by adding prices (TWAPs) for the time intervals and dividing
        // that by the number of intervals
        sma = 0;

        // Get prices at each tick
        priceAtTick = new uint256[](tickCumulatives.length - 1);
        for (uint32 i = 0; i < tickCumulatives.length - 1; i++) {
            int56 tickCumulativesDelta = tickCumulatives[
                tickCumulatives.length - 1 - i
            ] - tickCumulatives[tickCumulatives.length - 2 - i];
            int24 timeWeightedAverageTick = int24(
                tickCumulativesDelta / periodLength
            );
            // Always round to negative infinity (taken from Uniswap OracleLibrary's consult())
            if (
                tickCumulativesDelta < 0 &&
                (tickCumulativesDelta % periodLength != 0)
            ) timeWeightedAverageTick--;

            // Calculate the amount of token1 received in exchange for token0
            priceAtTick[i] = OracleLibrary.getQuoteAtTick(
                timeWeightedAverageTick,
                1,
                token0,
                token1
            );

            // Add the learned price to SMA
            sma = SafeMath.add(sma, priceAtTick[i]);
        }
        // Divide SMA with the number of intervals
        sma = sma.div(tickCumulatives.length - 1);
    }

    // Standard deviation of the prices in numOfPeriods periods of periodLength length. Also takes mean as this value is precomputed in the
    // bollinger function and used in several other places
    function standardDev(uint256[] memory pastPrices, uint256 mean)
        public
        returns (uint256 stdDev)
    {
        uint256 sumOfSquaredDev = 0;
        for (uint256 i = 0; i < pastPrices.length; i++) {
            sumOfSquaredDev += (pastPrices[i] - mean) * (pastPrices[i] - mean);
        }
        sqrt(sumOfSquaredDev / pastPrices.length);
    }

    // Maths
    function sqrt(uint256 y) internal pure returns (uint256 z) {
        if (y > 3) {
            z = y;
            uint256 x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        }
    }
}
