pragma solidity ^0.6.0; // compiled with 0.6.12

// import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/release-v3.0.0/contracts/token/ERC20/ERC20Pausable.sol";
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/release-v3.0.0/contracts/math/SafeMath.sol";
import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";



contract RTOToken {
    using SafeMath for uint256;

	address public deployer;
    AggregatorV3Interface internal priceFeed;

    struct Home {
        address renter;
        address owner;
        uint256 listPrice;
        uint256 totalEarned;
        uint256 earningsPercent;
    }

	mapping (address => bool) public Landlords;
	mapping (address => Home) public Homes;
	mapping (address => uint256) public balances;

	uint256 public totalSupply;

	event TokensMinted(
	    address earner,
	    uint256 amount
	    );

	event EarningsPercentChanged(
	    address renter,
	    uint256 newEarningsPercent
	    );

	event ListPriceChanged(
	    address renter,
	    uint256 newListPrice
	    );

	event RenterChanged(
	    address oldRenter,
	    address newRenter
	    );

	event HomePaidOff(
	    address renter
	    );


	constructor() public {
        deployer = msg.sender;
        priceFeed = AggregatorV3Interface(0x4a504064996F695dD8ADd2452645046289c4811C);
        totalSupply = 0;
    }

	function addLandlord(address _landlord) public {
	    require(msg.sender == deployer, "Only admin can call this function.");
	    Landlords[_landlord] = true;
	}

	function addHome(uint256 _listPrice, address _renter, uint256 _earningsPercent) public {
	    require(Landlords[msg.sender] == true, "Only approved landlords can list homes.");
	    Homes[_renter] = Home({
	        renter: _renter,
	        owner: msg.sender,
	        listPrice: _listPrice,
	        totalEarned: 0,
	        earningsPercent: _earningsPercent
	    });
	}

	function changeRenter(address _oldRenter, address _newRenter) public {
	    require(Homes[_oldRenter].owner == msg.sender, "Only the owner of this property can change the renter.");
	    Homes[_oldRenter].renter = _newRenter;
	    Homes[_newRenter] = Homes[_oldRenter];
	    delete Homes[_oldRenter];

	    emit RenterChanged(_oldRenter, _newRenter);
	}

	function changeListPrice(address _renter, uint256 _newListPrice) public {
	    require(Homes[_renter].owner == msg.sender, "Only the owner of this property can update the list price.");
	    Homes[_renter].listPrice = _newListPrice;

	    emit ListPriceChanged(_renter, _newListPrice);
	}

	function changeEarningsPercent(address _renter, uint256 _newEarningsPercent) public {
	    require(Homes[_renter].owner == msg.sender, "Only the owner of this property can update the earnings percentage.");
	    Homes[_renter].earningsPercent = _newEarningsPercent;

	    emit EarningsPercentChanged(_renter, _newEarningsPercent);
	}

    function getThePrice() public view returns (uint256) {
        (
            uint80 roundID,
            int price,
            uint startedAt,
            uint timeStamp,
            uint80 answeredInRound
        ) = priceFeed.latestRoundData();

        return uint256(price).div(1e8); // price that we get is USD*1e8 / ETH
    }

    function balanceOf(address _renter) public returns (uint256) {
        return balances[_renter];
    }

    function payRent(address payable _to) public payable {
        require(Landlords[_to] == true, "Rent must be sent to an approved landlord.");
        require(Homes[msg.sender].owner == _to, "Rent must be paid to the owner of the home.");

        _to.transfer(msg.value);

        uint256 amountToMint = msg.value.mul(uint256(getThePrice())).mul(Homes[msg.sender].earningsPercent).div(100);

        balances[msg.sender] += amountToMint;
        Homes[msg.sender].totalEarned += amountToMint;
        totalSupply += amountToMint;

        if (Homes[msg.sender].totalEarned > Homes[msg.sender].listPrice) {
            emit HomePaidOff(msg.sender);
        }

        emit TokensMinted(msg.sender, amountToMint);
    }
}
